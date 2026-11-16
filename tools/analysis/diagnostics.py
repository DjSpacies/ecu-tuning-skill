"""Diagnostic tests: each tells two or more causes apart from a log (and tune, if given).

Diagnostics only report. They never propose a table change; they say what a symptom most likely is, so the fuel and
ignition analyses are not fed the wrong cause. A test that lacks its channels or conditions is listed as not checked,
with the reason, rather than passed.

Thresholds in DIAG classify a symptom. They do not limit how far a tune may change (safety/limits.yaml does that).
Each is marked "practice" (a figure the KB reports from tuning practice) or "project default" (no published figure).
"""
import math, statistics

import gates
from analyses import Result, _align

DIAG = dict(
    koeo_good_kpa=1.5, koeo_bad_kpa=5.0,            # practice: about 1 kPa is normal; several kPa points to scaling or wiring
    koeo_settle_s=3.0,                               # project default: engine stopped this long before MAP is read as baro
    soak_pass_c=2.0, soak_investigate_c=5.0,         # practice
    soak_max_ect_c=40.0,                             # project default: compare temperatures only when the engine looks cold
    tps_closed_max_pct=1.0, tps_full_min_pct=95.0,   # project default
    rpm_spike=400.0,                                 # project default: one-sample departure from both neighbours
    ramp_ref_rpm_s=(400.0, 500.0),                   # practice: a high-gear road pull
    ramp_mismatch=0.25,                              # project default: pulls whose rates differ more are not comparable
    lean_over=0.10,                                  # practice: about 10 % leaner than target
    lean_min_s=0.1, brief_s=0.3, transient_s=1.0,    # project default
    overrun_tps_pct=5.0,                             # practice: closed throttle below about 5 to 10 %
    load_tps_pct=20.0,                               # project default: above this the engine is under load
    wot_tps_pct=90.0, pull_span_rpm=2000.0,          # project default (as in the capture review)
    cl_pin_min_pct=5.0, cl_pin_tol_pct=0.2, cl_pin_min_s=1.0, cl_pin_err=0.02,   # practice: error over 2 % with trim at its clamp
    cl_mask_trim_pct=3.0, cl_mask_err_pct=1.0,       # practice: trim over about 3 % with lambda within 1 %
    cell_min=20,                                     # as the fuel analysis
    slope_min_span_c=15.0, ect_slope_min_span_c=8.0, slope_min_sd_c=3.0,          # project default
    slope_min_cells=2, slope_agree=0.75, slope_cell_min=20,   # project default
    slope_implausible_pct=8.0,                       # project default: per 10 C, larger than a temperature correction plausibly is
    slope_ok_pct=1.0, slope_double_pct=2.0,          # per 10 C. practice: a double correction is about 3 % per 10 C
    dp_sag_kpa=20.0,                                 # practice: a steady sag of 10 to 20 kPa through a pull
    dp_ref_slope=0.7,                                # project default: rail rising this much per kPa of MAP is referenced
    duty_high_pct=85.0, duty_sat_pct=95.0, duty_mid_pct=75.0, duty_lean_pct=3.0,  # practice: 85 to 90 % ceiling; lean past 95 %
    ign_inversion_deg=1.0,                           # project default
    knock_band_rpm=500.0, knock_low_map_kpa=60.0, knock_noise_ratio=0.8,           # project default
    iat_rise_warn_c=15.0,                            # project default
    eth_step_pct=5.0, fuel_temp_range_c=(-30.0, 90.0),   # project default (plausibility, not a limit)
    oil_dip_frac=0.3, oil_recover_s=1.0, oil_min_rpm=2000.0, oil_window_s=2.0,    # practice: recovers within about a second
)

class Skip(Exception):
    """The test cannot run on this log; the message says what is missing."""

def _need(ch, *names):
    miss = [n for n in names if n not in ch]
    if miss: raise Skip("needs " + ", ".join(miss))

def _runs(mask):
    """[(start, end)] inclusive index ranges where mask is true."""
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]: j += 1
            out.append((i, j)); i = j + 1
        else: i += 1
    return out

def _pct(v, q):
    s = sorted(v); return s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))]

class Ctx:
    def __init__(self, log, tables, profile, d):
        self.log, self.ch, self.t, self.tables, self.profile, self.d = log, log.channels, log.time_s, tables or {}, profile, d
        self.dt = 1.0 / max(log.sample_rate_hz(), 1e-6)
        self.running = [r > gates.HEURISTIC["rpm_min"] for r in self.ch["rpm"]]
        self._reasons = self._fuel = self._pulls = self._target = None

    @property
    def reasons(self):
        if self._reasons is None: self._reasons = gates.classify(self.log)
        return self._reasons

    @property
    def fuel_reasons(self):
        if self._fuel is None: self._fuel = gates.classify(self.log, fuel=True)
        return self._fuel

    def baro(self, i):
        return self.ch["baro_kpa"][i] if "baro_kpa" in self.ch else 101.3

    def target(self):
        """Lambda target per sample, from the log or the tune's target table; None if neither."""
        if self._target is None:
            if "lambda_target" in self.ch: self._target = self.ch["lambda_target"]
            elif self.tables.get("lambda_target") is not None:
                tb = self.tables["lambda_target"]
                if tb.x_channel in self.ch and tb.y_channel in self.ch:
                    self._target = [tb.lookup(x, y) for x, y in zip(self.ch[tb.x_channel], self.ch[tb.y_channel])]
        return self._target

    def lambda_error(self, aligned=True):
        """measured/target - 1 per sample (positive is lean), with the transport delay applied; None where unknown."""
        tgt = self.target()
        if "lambda" not in self.ch or tgt is None: return None
        lam = _align(self.ch["lambda"], self.t, self.ch["rpm"], gates.HEURISTIC) if aligned else self.ch["lambda"]
        return [(m / g - 1.0) if m is not None and g and g > 0 else None for m, g in zip(lam, tgt)]

    def cell(self, i):
        """Operating cell for sample i: the fuel table's cell if available, else 500 rpm by 10 kPa bins."""
        tb = self.tables.get("ve")
        if tb is not None and tb.x_channel in self.ch and tb.y_channel in self.ch:
            r, c = tb.cell(self.ch[tb.x_channel][i], self.ch[tb.y_channel][i]); return (tb.x_axis[c], tb.y_axis[r])
        load = self.ch["map_kpa"][i] if "map_kpa" in self.ch else self.ch.get("tps", [0] * len(self.t))[i]
        return (round(self.ch["rpm"][i] / 500) * 500, round(load / 10) * 10)

    def pulls(self):
        """Full-throttle segments, split at gear changes, that span a useful rpm range: [(start, end)]."""
        if self._pulls is None:
            out = []
            if "tps" in self.ch:
                rpm = self.ch["rpm"]
                for a, b in _runs([x >= self.d["wot_tps_pct"] for x in self.ch["tps"]]):
                    s, top = a, rpm[a]
                    for k in range(a, b + 1):
                        if rpm[k] > top: top = rpm[k]
                        if rpm[k] < top - 300 or k == b:              # a shift or the end of the run
                            end = k - 1 if k < b or rpm[k] < top - 300 else k
                            seg_top = max(rpm[s:end + 1]) if end >= s else rpm[s]
                            if seg_top - rpm[s] >= self.d["pull_span_rpm"]: out.append((s, end))
                            s, top = k, rpm[k]
            self._pulls = out
        return self._pulls

def _f(diag, id_, severity, text, **kw): return dict(id=id_, severity=severity, text=text, diagnostic=diag, **kw)

# --- sensors ---------------------------------------------------------------------------------------------------

def map_baro_key_on(c):
    _need(c.ch, "map_kpa", "baro_kpa")
    rpm, t = c.ch["rpm"], c.t
    last_run, idx = None, []
    for i, r in enumerate(rpm):
        if r > 0: last_run = t[i]; continue
        if last_run is None or t[i] - last_run >= c.d["koeo_settle_s"]: idx.append(i)
    if len(idx) < 5: raise Skip("no engine-off samples; start logging with the key on before cranking")
    diff = statistics.median(c.ch["map_kpa"][i] - c.ch["baro_kpa"][i] for i in idx)
    a = abs(diff)
    sev = "info" if a <= c.d["koeo_good_kpa"] else ("warning" if a <= c.d["koeo_bad_kpa"] else "fault")
    text = (f"With the engine off, MAP reads {diff:+.1f} kPa from barometric pressure. " +
            ("That is normal." if sev == "info" else "A small offset; check MAP calibration before trusting load." if sev == "warning" else
             "That is too large for sensor tolerance: check the MAP sensor's calibration, wiring and reference first. Load and every table lookup depend on it."))
    return [_f("koeo-map-vs-baro", "map_baro_key_on", sev, text, value=round(diff, 2))]

def cold_soak_agreement(c):
    _need(c.ch, "ect", "iat")
    pre = [i for i in range(len(c.t)) if not c.running[i]]
    start = next((i for i, r in enumerate(c.running) if r), None)
    pre = [i for i in pre if start is None or i < start]
    if len(pre) < 5: raise Skip("no samples before the first start")
    e, a = statistics.median(c.ch["ect"][i] for i in pre), statistics.median(c.ch["iat"][i] for i in pre)
    if e > c.d["soak_max_ect_c"]: raise Skip(f"coolant was {e:.0f} C at key-on, so the engine was not cold-soaked")
    d = abs(e - a)
    sev = "info" if d <= c.d["soak_investigate_c"] else "warning"
    word = "agree" if d <= c.d["soak_pass_c"] else ("are plausibly close" if sev == "info" else "disagree")
    return [_f("cold-soak-temperature-agreement", "cold_soak_agreement", sev,
               f"At key-on, coolant {e:.0f} C and intake air {a:.0f} C {word} (difference {d:.1f} C)." +
               (" After a long soak they should read about the same; check each sensor's calibration curve and wiring." if sev == "warning" else
                " Valid only if the engine had soaked for several hours."), value=round(d, 1))]

def tps_endpoints(c):
    _need(c.ch, "tps")
    run = [x for x, r in zip(c.ch["tps"], c.running) if r]
    if len(run) < 20: raise Skip("the engine barely runs in this log")
    out = []
    lo, hi = _pct(run, 0.02), max(run)
    if min(run) < -0.5 or hi > 100.5:
        out.append(_f("tps-endpoints-and-sweep", "tps_out_of_range", "fault", f"Throttle reads {min(run):.1f} to {hi:.1f} %, outside 0 to 100: recalibrate the end points."))
    if lo > c.d["tps_closed_max_pct"]:
        out.append(_f("tps-endpoints-and-sweep", "tps_closed_offset", "warning", f"Closed throttle reads about {lo:.1f} %, not 0. Recalibrate the closed point, unless an electronic throttle deliberately holds the blade open at idle.", value=round(lo, 1)))
    if c.d["wot_tps_pct"] * 0.85 <= hi < c.d["tps_full_min_pct"]:
        out.append(_f("tps-endpoints-and-sweep", "tps_full_short", "warning", f"Throttle peaks at {hi:.1f} %. If the pedal was flat, the full point needs recalibrating, and full-throttle tables are not being reached.", value=round(hi, 1)))
    if not out: out.append(_f("tps-endpoints-and-sweep", "tps_endpoints_ok", "info", f"Throttle reads {lo:.1f} % closed and peaks at {hi:.1f} %."))
    return out

def trigger_integrity(c):
    rpm, out = c.ch["rpm"], []
    if "trigger_errors" in c.ch:
        te = c.ch["trigger_errors"]
        inc = sum(1 for i in range(1, len(te)) if te[i] > te[i - 1] and c.running[i])
        if inc: out.append(_f("trigger-error-counter-during-pull", "trigger_errors", "fault", f"The trigger error counter rose {inc} times while the engine ran. Fix the trigger before tuning: misfires and false knock follow from it.", value=inc))
    s, spikes = c.d["rpm_spike"], []
    for i in range(1, len(rpm) - 1):
        a, b, n = rpm[i - 1], rpm[i], rpm[i + 1]
        if b > 500 and abs(b - a) > s and abs(b - n) > s and (b - a) * (b - n) > 0 and abs(a - n) < s / 2: spikes.append(i)
    if spikes:
        out.append(_f("rpm-rate-plausibility-on-ramp", "rpm_spikes", "warning",
                      f"{len(spikes)} single-sample rpm spikes (first at {c.t[spikes[0]]:.1f} s). An engine cannot change speed that fast; this points to trigger noise or a marginal trigger signal.", value=len(spikes)))
    if not out: out.append(_f("rpm-rate-plausibility-on-ramp", "trigger_ok", "info", "No isolated rpm spikes" + (" and no trigger errors." if "trigger_errors" in c.ch else "; the log has no trigger error counter.")))
    return out

def ethanol_plausibility(c):
    if "ethanol_pct" not in c.ch and "fuel_temp" not in c.ch: raise Skip("needs ethanol_pct or fuel_temp")
    out = []
    if "ethanol_pct" in c.ch:
        e = [x for x, r in zip(c.ch["ethanol_pct"], c.running) if r]
        if e:
            lo, hi = min(e), max(e)
            if lo < 0 or hi > 100: out.append(_f("flex-sensor-plausibility-and-fault-state", "ethanol_out_of_range", "fault", f"Ethanol content reads {lo:.0f} to {hi:.0f} %, outside 0 to 100: the sensor or its input is faulty, and the blend is not trustworthy."))
            elif hi - lo > c.d["eth_step_pct"]: out.append(_f("flex-content-settling", "ethanol_moving", "warning", f"Ethanol content moved from {lo:.0f} to {hi:.0f} % during the log. Unless the tank was just filled and the new fuel is still reaching the sensor, the sensor is suspect. Fuel results from a log with moving content mix two fuels.", value=round(hi - lo, 1)))
            else: out.append(_f("flex-content-settling", "ethanol_steady", "info", f"Ethanol content stayed at {lo:.0f} to {hi:.0f} %.", value=round(statistics.median(e), 1)))
    if "fuel_temp" in c.ch:
        ft = c.ch["fuel_temp"]; lo, hi = c.d["fuel_temp_range_c"]
        if min(ft) < lo or max(ft) > hi: out.append(_f("flex-sensor-plausibility-and-fault-state", "fuel_temp_implausible", "fault", f"Fuel temperature reads {min(ft):.0f} to {max(ft):.0f} C, which is not plausible. Check the sensor and what the ECU applies when it faults."))
    return out

# --- fuel ------------------------------------------------------------------------------------------------------

def lean_events(c):
    _need(c.ch, "lambda")
    tgt = c.target()
    if tgt is None: raise Skip("needs a lambda target from the log or tune")
    ch, lam, d = c.ch, c.ch["lambda"], c.d
    mask = [c.running[i] and g > 0 and lam[i] > g * (1 + d["lean_over"]) for i, g in enumerate(tgt)]
    events = [(a, b) for a, b in _runs(mask) if c.t[b] - c.t[a] + c.dt >= d["lean_min_s"]]
    if not events: return [_f("false-lean-during-cut-or-misfire", "lean_events_none", "info", f"Lambda never ran more than {d['lean_over']:.0%} leaner than target for {d['lean_min_s']:g} s or longer.")]
    back = max(1, int(0.3 / c.dt))
    counts, real, brief = {}, [], []
    for a, b in events:
        w0 = max(0, a - back - int(gates.lambda_delay_s(ch["rpm"][a]) / c.dt))
        win = range(w0, b + 1)
        cut = any(ch.get("fuel_cut", [0] * len(c.t))[i] or ch.get("limiter_active", [0] * len(c.t))[i] for i in win)
        tps = [ch["tps"][i] for i in win] if "tps" in ch else None
        if cut: kind = "cut"
        elif tps and min(tps) < d["overrun_tps_pct"]: kind = "overrun"
        elif tps and (max(tps) - min(tps) > 20) and c.t[b] - c.t[a] <= d["transient_s"]: kind = "transient"
        elif tps and min(tps) >= d["load_tps_pct"]:
            kind = "brief" if c.t[b] - c.t[a] + c.dt <= d["brief_s"] else "under_load"
        else: kind = "light_load"
        counts[kind] = counts.get(kind, 0) + 1
        info = dict(t=round(c.t[a], 1), s=round(c.t[b] - c.t[a] + c.dt, 2), rpm=round(ch["rpm"][a]), lam=round(max(lam[a:b + 1]), 3), target=round(tgt[a], 3),
                    map=round(ch["map_kpa"][a]) if "map_kpa" in ch else None)
        if kind == "under_load": real.append(info)
        if kind == "brief": brief.append(info)
    out = [_f("overrun-vs-lean", "lean_events", "info", "Lean events by cause: " + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in sorted(counts.items())) +
              ". Cut, overrun and throttle-transient events are oxygen from unburnt or unsettled charge, not mixture; the analyses exclude them.", value=counts)]
    if real:
        w = max(real, key=lambda x: x["lam"] / x["target"])
        out.append(_f("false-lean-during-cut-or-misfire", "lean_under_load", "fault",
                      f"{len(real)} sustained lean events under load with no cut or throttle change, worst {w['lam']} against target {w['target']} at {w['rpm']} rpm, {w['map']} kPa ({w['t']} s). These are real lean running; stop load work until the cause is known.", events=real[:10]))
    if brief:
        out.append(_f("false-lean-during-cut-or-misfire", "lean_brief_under_load", "warning",
                      f"{len(brief)} brief lean spikes under load with normal lambda either side (first at {brief[0]['t']} s, {brief[0]['rpm']} rpm). A short spike from a steady mixture is more often a misfire or sensor glitch than fuelling; check ignition before fuel.", events=brief[:10]))
    return out

def cl_trim_saturation(c):
    _need(c.ch, "fuel_trim")
    tr = c.ch["fuel_trim"]
    idx = [i for i, why in enumerate(c.reasons) if why is None]
    if len(idx) < 20: raise Skip("too few steady samples")
    hi, lo = max(tr[i] for i in idx), min(tr[i] for i in idx)
    out = []
    err = c.lambda_error(aligned=False)
    for ext in (hi, lo):
        if abs(ext) < c.d["cl_pin_min_pct"]: continue
        pinned = [i for i in idx if abs(tr[i] - ext) <= c.d["cl_pin_tol_pct"]]
        if len(pinned) * c.dt < c.d["cl_pin_min_s"]: continue
        still = None
        if err is not None:
            e = [err[i] for i in pinned if err[i] is not None]
            still = statistics.median(e) if e else None
        if still is not None and abs(still) > c.d["cl_pin_err"]:
            rp = [c.ch["rpm"][i] for i in pinned]; where = f"mostly {_pct(rp, 0.1):.0f} to {_pct(rp, 0.9):.0f} rpm"
            if "map_kpa" in c.ch: mp = [c.ch["map_kpa"][i] for i in pinned]; where += f", {_pct(mp, 0.1):.0f} to {_pct(mp, 0.9):.0f} kPa"
            if "tps" in c.ch: where += f", throttle about {statistics.median(c.ch['tps'][i] for i in pinned):.0f} %"
            out.append(_f("closed-loop-trim-saturation", "cl_trim_pinned", "warning",
                          f"Closed-loop trim sits at {ext:+.1f} % for {len(pinned) * c.dt:.0f} s ({where}) while lambda is still {still * 100:+.1f} % from target. The trim is at its clamp, so it understates the error; the base table there is off by the trim plus the remaining error.",
                          value=ext, seconds=round(len(pinned) * c.dt, 1), lambda_error_pct=round(still * 100, 1)))
        else:
            out.append(_f("closed-loop-trim-saturation", "cl_trim_at_extreme", "info", f"Closed-loop trim spends {len(pinned) * c.dt:.0f} s at its extreme of {ext:+.1f} % but lambda reaches target there.", value=ext))
    if not out: out.append(_f("closed-loop-trim-saturation", "cl_trim_in_range", "info", f"Closed-loop trim stays between {lo:+.1f} and {hi:+.1f} % with no sign of a clamp."))
    return out

def cl_masking(c):
    _need(c.ch, "fuel_trim", "lambda")
    err = c.lambda_error(aligned=False)
    if err is None: raise Skip("needs a lambda target from the log or tune")
    cells = {}
    for i, why in enumerate(c.reasons):
        if why is None and err[i] is not None: cells.setdefault(c.cell(i), []).append((c.ch["fuel_trim"][i], err[i]))
    masked = []
    for k, v in cells.items():
        if len(v) < c.d["cell_min"]: continue
        mt, me = statistics.median(x for x, _ in v), statistics.median(e for _, e in v) * 100
        if abs(mt) >= c.d["cl_mask_trim_pct"] and abs(me) < c.d["cl_mask_err_pct"]: masked.append(dict(rpm=k[0], load=k[1], trim_pct=round(mt, 1), samples=len(v)))
    if not cells: raise Skip("too few steady samples")
    if not masked: return [_f("true-base-error-under-closed-loop", "cl_masking_none", "info", "No cell shows lambda on target only because closed loop is trimming hard.")]
    masked.sort(key=lambda m: -abs(m["trim_pct"]))
    top = ", ".join(f"{m['rpm']:g} rpm/{m['load']:g} at {m['trim_pct']:+.1f} %" for m in masked[:6])
    return [_f("true-base-error-under-closed-loop", "cl_masking", "warning",
               f"In {len(masked)} cells lambda reads on target because closed loop is trimming {c.d['cl_mask_trim_pct']:g} % or more ({top}). The base table is off by about that trim. Lambda alone hides it: judge the base table with closed loop off, or from the trims (the trim channel's sign convention must be confirmed for this ECU first).",
               cells=masked[:20])]

def _residual_slope(c, var, idx, err):
    """Pooled within-cell slope of err against var, so operating point does not masquerade as temperature."""
    cells = {}
    for i in idx: cells.setdefault(c.cell(i), []).append((c.ch[var][i], err[i]))
    sxy = sxx = 0.0; n = 0; signs = []
    for v in cells.values():
        if len(v) < c.d["slope_cell_min"]: continue
        mx, my = statistics.fmean(x for x, _ in v), statistics.fmean(y for _, y in v)
        cx = sum((x - mx) ** 2 for x, _ in v)
        if math.sqrt(cx / len(v)) < 1.0: continue                       # this cell saw one temperature only
        cxy = sum((x - mx) * (y - my) for x, y in v)
        sxy += cxy; sxx += cx; n += len(v); signs.append((cxy / cx, len(v)))
    if n < 50 or sxx <= 0 or len(signs) < c.d["slope_min_cells"]: return None, 0.0, 0
    slope = sxy / sxx
    if abs(slope) * 1000 >= c.d["slope_ok_pct"]:                        # a real slope must have the same sign in most cells
        agree = sum(w for k, w in signs if k * slope > 0) / sum(w for _, w in signs)
        if agree < c.d["slope_agree"]: return None, 0.0, 0                  # cells disagree: something other than temperature
    return slope * 10 * 100, math.sqrt(sxx / n), n     # % per 10 C, within-cell spread of var, samples

def _caveats(c, idx, var):
    """Reasons a temperature relationship may be something else that changes over the same time."""
    out, cnt = [], {}
    for i in idx: cnt[c.cell(i)] = cnt.get(c.cell(i), 0) + 1
    idx = [i for i in idx if cnt[c.cell(i)] >= c.d["slope_cell_min"]]
    if "ethanol_pct" in c.ch:
        e = [c.ch["ethanol_pct"][i] for i in idx]
        if max(e) - min(e) > c.d["eth_step_pct"] / 2: out.append("ethanol content also changed across these samples")
    idle = sum(1 for i in idx if c.ch["rpm"][i] < 1300 and c.ch.get("tps", [0] * len(c.t))[i] < 5) / max(len(idx), 1)
    if idle > 0.6: out.append("most samples are at idle, where idle control, heat soak and fan load also change with temperature")
    return out

def _temp_inputs(c, var, lo_c=None):
    """Samples and error signal for a temperature-slope test. Prefers lambda error with closed loop not trimming."""
    err = c.lambda_error()
    if err is None: raise Skip("needs lambda and a lambda target")
    idx = [i for i, why in enumerate(c.fuel_reasons) if why is None and err[i] is not None and (lo_c is None or c.ch["ect"][i] >= lo_c)]
    return idx, err, "lambda error"

def iat_compensation_slope(c):
    _need(c.ch, "iat", "lambda")
    idx, err, sig = _temp_inputs(c, "iat")
    if len(idx) < 50:
        raise Skip("too few samples with closed loop not trimming; log with closed loop off" if "fuel_trim" in c.ch else "too few steady warm samples")
    span = max(c.ch["iat"][i] for i in idx) - min(c.ch["iat"][i] for i in idx)
    if span < c.d["slope_min_span_c"]: raise Skip(f"intake temperature varied only {span:.0f} C in usable samples; needs {c.d['slope_min_span_c']:g} C or more")
    slope, sd, n = _residual_slope(c, "iat", idx, err)
    if slope is None or sd < c.d["slope_min_sd_c"]: raise Skip("intake temperature did not vary enough within enough operating cells, or the cells disagree")
    ok, dbl = c.d["slope_ok_pct"], c.d["slope_double_pct"]
    if abs(slope) < ok: sev, why = "info", "The air-temperature correction looks right."
    elif slope < 0: sev, why = "warning", "Mixture goes richer as intake air heats: the air-temperature correction is missing or too weak."
    elif slope >= dbl: sev, why = "warning", "Mixture goes leaner as intake air heats, by about the size of the correction itself: it is probably applied twice (a model correction plus a manual table)."
    else: sev, why = "warning", "Mixture goes leaner as intake air heats: the air-temperature correction is too strong."
    cav = _caveats(c, idx, "iat")
    if sev == "warning" and abs(slope) > c.d["slope_implausible_pct"]: why += " The slope is larger than a temperature correction plausibly is, so check for heat soak or another drift too."
    return [_f("iat-compensation-slope", "iat_compensation_slope", sev, f"Within the same cells, {sig} changes {slope:+.1f} % per 10 C of intake temperature ({n} samples). {why} Fix this before editing fuel cells, or the table absorbs a temperature effect." + (" Caution: " + "; ".join(cav) + "." if cav else ""), value=round(slope, 2))]

def hidden_coolant_trim(c):
    _need(c.ch, "ect", "lambda")
    warm = gates.HEURISTIC["ect_min_c"]
    idx, err, sig = _temp_inputs(c, "ect", warm)
    if len(idx) < 50: raise Skip("too few warm samples with closed loop not trimming")
    span = max(c.ch["ect"][i] for i in idx) - min(c.ch["ect"][i] for i in idx)
    if span < c.d["ect_slope_min_span_c"]: raise Skip(f"coolant varied only {span:.0f} C above {warm:g} C")
    slope, sd, n = _residual_slope(c, "ect", idx, err)
    if slope is None or sd < 1.0: raise Skip("coolant did not vary enough within enough operating cells, or the cells disagree")
    if abs(slope) < c.d["slope_ok_pct"]:
        return [_f("hidden-coolant-trim", "coolant_trim_neutral", "info", f"Above {warm:g} C, {sig} does not follow coolant ({slope:+.1f} % per 10 C).", value=round(slope, 2))]
    cav = _caveats(c, idx, "ect")
    big = abs(slope) > c.d["slope_implausible_pct"]
    why = ("That is larger than a coolant correction plausibly is, so something else that rises with coolant (heat soak, idle control, fan load) is more likely." if big else
           "A coolant or warm-up correction is probably still active in the operating range; check those tables end at neutral before editing the base table.")
    return [_f("hidden-coolant-trim", "coolant_trim_active", "warning", f"Above {warm:g} C, {sig} changes {slope:+.1f} % per 10 C of coolant within the same cells ({n} samples). {why}" + (" Caution: " + "; ".join(cav) + "." if cav else ""), value=round(slope, 2))]

def fuel_pressure_tracking(c):
    ch = c.ch
    if "fuel_dp_kpa" in ch: dp, src = ch["fuel_dp_kpa"], "logged differential"
    elif "fuel_pressure_kpa" in ch and "map_kpa" in ch: dp, src = [p - (m - c.baro(i)) for i, (p, m) in enumerate(zip(ch["fuel_pressure_kpa"], ch["map_kpa"]))], "rail minus manifold (rail sensor assumed gauge)"
    else: raise Skip("needs fuel_dp_kpa, or fuel_pressure_kpa and map_kpa")
    _need(ch, "map_kpa")
    idx = [i for i, r in enumerate(c.running) if r and (ch.get("fuel_cut") is None or not ch["fuel_cut"][i])]
    if len(idx) < 50: raise Skip("the engine barely runs in this log")
    maps = [ch["map_kpa"][i] for i in idx]
    lo_map, hi_map = _pct(maps, 0.25), _pct(maps, 0.95)
    base = [dp[i] for i in idx if ch["map_kpa"][i] <= lo_map]
    load_idx = [i for i in idx if ch["map_kpa"][i] >= hi_map and (("tps" not in ch) or ch["tps"][i] >= c.d["wot_tps_pct"])]
    if len(load_idx) < 10: raise Skip("no sustained full-load samples")
    b, l = statistics.median(base), statistics.median(dp[i] for i in load_idx)
    if b <= 0: raise Skip("differential fuel pressure does not read as kPa")
    sag = b - l
    referenced = None
    if "fuel_pressure_kpa" in ch and len(set(maps)) > 1:
        xs, ys = maps, [ch["fuel_pressure_kpa"][i] for i in idx]
        mx, my = statistics.fmean(xs), statistics.fmean(ys)
        sxx = sum((x - mx) ** 2 for x in xs)
        if sxx > 0: referenced = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx >= c.d["dp_ref_slope"]
    flow = math.sqrt(max(l, 0) / b)
    kind = "manifold-referenced" if referenced else ("fixed-pressure" if referenced is False else "unknown-reference")
    if sag > c.d["dp_sag_kpa"] and referenced is not False:
        return [_f("differential-pressure-tracking", "fuel_dp_sag", "warning",
                   f"Differential fuel pressure ({src}) is {b:.0f} kPa at light load but {l:.0f} kPa at full load, a {sag:.0f} kPa fall. On a {kind} system it should hold steady, so the pump, its voltage or the supply is running short. Injectors flow about {(1 - flow) * 100:.0f} % less than their calibration assumes there, which reads as lean at the top of the map.",
                   value=round(sag, 1), base_kpa=round(b), load_kpa=round(l))]
    sev = "info"
    note = f" On a fixed-pressure system that is expected: injectors flow about {(1 - flow) * 100:.0f} % less on boost, and the fuel model must compensate." if referenced is False and sag > 0 else ""
    return [_f("differential-pressure-tracking", "fuel_dp_ok", sev, f"Differential fuel pressure ({src}) is {b:.0f} kPa at light load and {l:.0f} kPa at full load.{note}", value=round(sag, 1))]

def duty_lambda_departure(c):
    _need(c.ch, "inj_duty", "lambda")
    err = c.lambda_error()
    if err is None: raise Skip("needs a lambda target from the log or tune")
    wot = [i for i in range(len(c.t)) if c.running[i] and err[i] is not None and c.reasons[i] in (None, "rpm_transient") and c.ch.get("tps", [100] * len(c.t))[i] >= c.d["wot_tps_pct"]]
    if len(wot) < 20: raise Skip("too few full-throttle samples")
    duty = c.ch["inj_duty"]; peak = max(duty[i] for i in wot)
    sat = [err[i] for i in wot if duty[i] >= c.d["duty_sat_pct"]]
    mid = [err[i] for i in wot if duty[i] < c.d["duty_mid_pct"]]
    out = []
    if len(sat) >= 5 and statistics.median(sat) * 100 > c.d["duty_lean_pct"]:
        out.append(_f("duty-ceiling-and-lambda-departure", "injector_saturation", "fault", f"With injector duty at {c.d['duty_sat_pct']:g} % or more, lambda runs {statistics.median(sat) * 100:+.1f} % leaner than target: the injectors have run out. More fuel table cannot fix this.", value=peak))
    if len(mid) >= 10 and statistics.median(mid) * 100 > c.d["duty_lean_pct"]:
        out.append(_f("duty-ceiling-and-lambda-departure", "lean_with_duty_headroom", "warning", f"At full throttle with duty under {c.d['duty_mid_pct']:g} %, lambda runs {statistics.median(mid) * 100:+.1f} % lean. The injectors have headroom, so check fuel pressure and the pump before the fuel table.", value=peak))
    if not out:
        sev = "warning" if peak >= c.d["duty_high_pct"] else "info"
        out.append(_f("duty-ceiling-and-lambda-departure", "duty_headroom", sev, f"Peak full-throttle injector duty is {peak:.0f} %" + (", close to the usable ceiling; there is little headroom for more power." if sev == "warning" else ", and lambda holds target as duty rises."), value=peak))
    return out

# --- tables ----------------------------------------------------------------------------------------------------

def load_axis_saturation(c):
    out, done = [], 0
    for role in ("ve", "ve_2", "ign_base", "ign_base_2", "lambda_target"):
        tb = c.tables.get(role)
        if tb is None or tb.x_channel not in c.ch or tb.y_channel not in c.ch: continue
        done += 1
        idx = [i for i, r in enumerate(c.running) if r]
        ys, xs = [c.ch[tb.y_channel][i] for i in idx], [c.ch[tb.x_channel][i] for i in idx]
        over_y = sum(1 for y in ys if y > tb.y_axis[-1]); over_x = sum(1 for x in xs if x > tb.x_axis[-1])
        name = tb.native_name or role
        if over_y: out.append(_f("load-axis-saturation", f"axis_exceeded_{role}", "warning", f"{name}: load reached {max(ys):.0f} against a top breakpoint of {tb.y_axis[-1]:g} in {over_y * c.dt:.1f} s of running. The ECU holds the top row there, so that region is untuned; extend the axis.", value=round(max(ys), 1)))
        if over_x: out.append(_f("load-axis-saturation", f"rpm_axis_exceeded_{role}", "warning", f"{name}: rpm reached {max(xs):.0f} against a top breakpoint of {tb.x_axis[-1]:g}.", value=round(max(xs))))
        if role == "ve" and c.pulls():
            w = [c.ch[tb.y_channel][i] for a, b in c.pulls() for i in range(a, b + 1)]
            p5, p95 = _pct(w, 0.05), _pct(w, 0.95)
            ax = tb.y_axis
            lo_k = max([k for k, y in enumerate(ax) if y <= p5] or [0]); hi_k = min([k for k, y in enumerate(ax) if y >= p95] or [len(ax) - 1])
            rows = ax[lo_k:hi_k + 1]
            out.append(_f("wot-row-access", "wot_rows_used", "info", f"{name}: full-throttle load spans {p5:.0f} to {p95:.0f}, so the rows used are {', '.join(f'{y:g}' for y in rows)}. Full-load edits belong in those rows, not the top row if it is never reached.", rows=rows))
    if not done: raise Skip("needs a tune with tables whose axis channels are logged")
    if not out: out.append(_f("load-axis-saturation", "axes_cover_log", "info", "The table axes cover every operating point in the log."))
    return out

def ignition_load_monotonicity(c):
    out, done = [], 0
    for role in ("ign_base", "ign_base_2"):
        tb = c.tables.get(role)
        if tb is None: continue
        done += 1
        knee = {"map_kpa": 100.0, "mgp_kpa": 0.0}.get(tb.y_channel)        # from atmospheric pressure up
        start = next((k for k, y in enumerate(tb.y_axis) if y >= knee), len(tb.y_axis) // 2) if knee is not None else len(tb.y_axis) // 2
        inv = [(tb.y_axis[r + 1], tb.x_axis[col], tb.values[r + 1][col] - tb.values[r][col]) for r in range(start, len(tb.y_axis) - 1) for col in range(len(tb.x_axis))
               if tb.values[r + 1][col] - tb.values[r][col] > c.d["ign_inversion_deg"]]
        if inv:
            inv.sort(key=lambda x: -x[2])
            out.append(_f("ignition-load-monotonicity", f"ign_load_inversion_{role}", "warning", f"{tb.native_name or role}: {len(inv)} cells at boost or high load have more advance than the cell below them (largest {inv[0][2]:+.1f} deg at {inv[0][1]:g} rpm, load {inv[0][0]:g}). More load normally needs less advance; review them as possible copy or entry errors.",
                          cells=[dict(load=a, rpm=b, step=round(s, 1)) for a, b, s in inv[:20]]))
    if not done: raise Skip("needs an ignition table")
    if not out: out.append(_f("ignition-load-monotonicity", "ign_load_monotonic", "info", "Ignition advance falls or holds as load rises at every rpm in the high-load region."))
    return out

# --- knock -----------------------------------------------------------------------------------------------------

def knock_noise_vs_load(c):
    _need(c.ch, "knock_level")
    ch, d = c.ch, c.d
    low_of = (lambda i: ch["map_kpa"][i] < d["knock_low_map_kpa"]) if "map_kpa" in ch else (lambda i: ch["tps"][i] < d["load_tps_pct"])
    high_of = (lambda i: ch["map_kpa"][i] >= c.baro(i) * 0.95) if "map_kpa" in ch else (lambda i: ch["tps"][i] >= d["wot_tps_pct"])
    bands = {}
    for i, why in enumerate(c.reasons):
        if why not in (None, "rpm_transient"): continue
        b = int(ch["rpm"][i] // d["knock_band_rpm"] * d["knock_band_rpm"])
        g = "low" if low_of(i) else ("high" if high_of(i) else None)
        if g: bands.setdefault(b, {"low": [], "high": []})[g].append(ch["knock_level"][i])
    noise, load, blind = [], [], []
    for b, g in sorted(bands.items()):
        if len(g["high"]) < 10: continue
        if len(g["low"]) < 10: blind.append(b); continue
        lo, hi = _pct(g["low"], 0.9), _pct(g["high"], 0.9)
        (noise if hi <= 0 or lo / hi >= d["knock_noise_ratio"] else load).append(b)
    c.knock_bands = dict(noise=set(noise), blind=set(blind))
    if not (noise or load or blind): raise Skip("too few high-load samples")
    out = []
    if noise: out.append(_f("knock-mechanical-vs-combustion", "knock_noise_floor", "warning", f"At {', '.join(f'{b}' for b in noise)} rpm the knock level is about as high at light load as at full load: what the sensor hears there is mostly engine noise. Raise the threshold over the noise floor there, or knock control will retard on noise.", bands=noise))
    if load: out.append(_f("knock-mechanical-vs-combustion", "knock_rises_with_load", "info", f"At {', '.join(f'{b}' for b in load)} rpm the knock level rises with load above the light-load floor; a load-driven rise can be knock and should be confirmed by ear or by response to timing.", bands=load))
    if blind: out.append(_f("mechanical-noise-persistence", "knock_floor_unmeasured", "warning", f"At {', '.join(f'{b}' for b in blind)} rpm there is full-load data but no light-load data, so noise cannot be told from knock there. Record light-load running through those rpm.", bands=blind))
    if "knock_threshold" in ch:
        hi = [(ch["knock_level"][i], ch["knock_threshold"][i]) for i, why in enumerate(c.reasons) if why is None and ch["knock_threshold"][i] > 0 and high_of(i)]
        if hi:
            over = sum(1 for lv, th in hi if lv > th) / len(hi); m = _pct([lv / th for lv, th in hi], 0.95)
            out.append(_f("knock-threshold-margin", "knock_threshold_margin", "warning" if over > 0.01 else "info", f"At full load the knock level reaches {m:.0%} of the threshold (95th percentile) and exceeds it in {over:.1%} of samples.", value=round(m, 2)))
    return out

def knock_repeatability(c):
    ch = c.ch
    if "knock_count" in ch: ev = [i for i in range(1, len(c.t)) if ch["knock_count"][i] > ch["knock_count"][i - 1]]
    elif "knock_level" in ch and "knock_threshold" in ch:
        # The ECU's own count is better; a crossing at idle or light load is usually outside the knock control window.
        loaded = (lambda i: ch["map_kpa"][i] >= 0.7 * c.baro(i)) if "map_kpa" in ch else (lambda i: ch.get("tps", [100] * len(c.t))[i] >= c.d["load_tps_pct"])
        ev = [i for i in range(1, len(c.t)) if c.running[i] and loaded(i) and ch["knock_level"][i] > ch["knock_threshold"][i] > 0 and ch["knock_level"][i - 1] <= ch["knock_threshold"][i - 1]]
    else: raise Skip("needs knock_count, or knock_level and knock_threshold")
    if not ev: return [_f("repeatable-vs-isolated-retard", "knock_none", "info", "No knock events in the log; that is not proof there was none.")]
    pulls = c.pulls(); band = c.d["knock_band_rpm"]
    where = {}
    for i in ev:
        p = next((k for k, (a, b) in enumerate(pulls) if a <= i <= b), None)
        where.setdefault(int(ch["rpm"][i] // band * band), set()).add(p if p is not None else f"t{int(c.t[i])}")
    rep = sorted(b for b, s in where.items() if sum(1 for x in s if isinstance(x, int)) >= 2)
    iso = sorted(b for b in where if b not in rep)
    kb = getattr(c, "knock_bands", dict(noise=set(), blind=set()))
    unsure = [b for b in rep if b in kb["noise"] or b in kb["blind"]]
    sure = [b for b in rep if b not in unsure]
    out = []
    if sure: out.append(_f("repeatable-vs-isolated-retard", "knock_repeatable", "fault", f"Knock recurs in the same rpm band on more than one pull ({', '.join(map(str, sure))} rpm) where the sensor's noise floor is known to be lower: treat it as a timing or mixture problem in those cells, not a stray event.", bands=sure))
    if unsure: out.append(_f("knock-mechanical-vs-combustion", "knock_repeatable_unconfirmed", "warning", f"Knock recurs on more than one pull at {', '.join(map(str, unsure))} rpm, but the noise floor there is high or unmeasured, so it may be mechanical noise that repeats with rpm. Confirm by ear (audio knock detection) or with light-load data at that rpm before changing timing; until then do not add advance there.", bands=unsure))
    if iso: out.append(_f("repeatable-vs-isolated-retard", "knock_isolated", "warning", f"Knock at {', '.join(map(str, iso))} rpm happened on one pass only. A single event is often noise or a one-off (for example the first hard pull after cruising); repeat the pull before changing timing.", bands=iso))
    return out

# --- run conditions --------------------------------------------------------------------------------------------

def pull_conditions(c):
    pulls = c.pulls()
    if not pulls: raise Skip("no full-throttle pull")
    ch, out, rates, rows = c.ch, [], [], []
    for a, b in pulls:
        top = max(range(a, b + 1), key=lambda i: ch["rpm"][i])
        dur = c.t[top] - c.t[a]
        rate = (ch["rpm"][top] - ch["rpm"][a]) / dur if dur > 0 else 0.0
        rates.append(rate)
        row = dict(t=round(c.t[a], 1), rpm_from=round(ch["rpm"][a]), rpm_to=round(ch["rpm"][top]), rpm_per_s=round(rate))
        if "gear" in ch: row["gear"] = ch["gear"][a]
        if "iat" in ch: row["iat_rise_c"] = round(max(ch["iat"][a:b + 1]) - ch["iat"][a], 1)
        rows.append(row)
    lo, hi = c.d["ramp_ref_rpm_s"]
    out.append(_f("ramp-rate-check", "pull_rates", "info", f"{len(pulls)} pulls at " + ", ".join(f"{r:.0f}" for r in rates) + f" rpm/s. A high-gear road pull is typically about {lo:g} to {hi:g} rpm/s; much faster pulls load the engine for less time and read leaner and with less knock than sustained load.", pulls=rows))
    if len(rates) > 1 and (max(rates) - min(rates)) / max(max(rates), 1) > c.d["ramp_mismatch"]:
        out.append(_f("run-to-run-spread-vs-change", "pulls_not_comparable", "info", "Pull rates differ widely (different gears or conditions), so compare like with like only."))
    hot = [r for r in rows if r.get("iat_rise_c", 0) > c.d["iat_rise_warn_c"]]
    if hot: out.append(_f("intercooler-heat-soak", "iat_rise_in_pull", "warning", f"Intake temperature rose by up to {max(r['iat_rise_c'] for r in hot):.0f} C within a pull: the intercooler or charge path is heat soaking, and later pulls will run with less margin.", value=max(r["iat_rise_c"] for r in hot)))
    return out

def oil_pressure_dips(c):
    _need(c.ch, "oil_pressure_kpa")
    op, rpm, d, ch = c.ch["oil_pressure_kpa"], c.ch["rpm"], c.d, c.ch
    # Oil pressure follows rpm, so each sample is compared with this log's own typical pressure at that rpm.
    band = 500.0; per = {}
    for i, r in enumerate(rpm):
        if r >= d["oil_min_rpm"] and ("ect" not in ch or ch["ect"][i] >= gates.HEURISTIC["ect_min_c"]): per.setdefault(int(r // band), []).append(op[i])
    ref_of = {k: statistics.median(v) for k, v in per.items() if len(v) >= 20}
    if not ref_of: raise Skip(f"too little warm running above {d['oil_min_rpm']:g} rpm")
    rec = max(1, int(d["oil_recover_s"] / c.dt))
    low = lambda i: rpm[i] >= d["oil_min_rpm"] and int(rpm[i] // band) in ref_of and ref_of[int(rpm[i] // band)] > 50 and op[i] < (1 - d["oil_dip_frac"]) * ref_of[int(rpm[i] // band)]
    dips, drops = [], []
    for a, b in _runs([low(i) for i in range(len(op))]):
        ctx = "under load" if "tps" in ch and ch["tps"][a] >= 50 else "throttle closed"
        if ctx == "throttle closed" and "vehicle_speed" in ch and b > a:
            dv = (ch["vehicle_speed"][min(b + rec, len(op) - 1)] - ch["vehicle_speed"][a]) / max(c.t[min(b + rec, len(op) - 1)] - c.t[a], 1e-6)
            if dv < -10: ctx = "braking"
        ev = dict(t=round(c.t[a], 1), rpm=round(rpm[a]), expected_kpa=round(ref_of[int(rpm[a] // band)]), to_kpa=round(min(op[a:b + 1])), s=round((b - a + 1) * c.dt, 2), context=ctx)
        (dips if b - a + 1 <= rec else drops).append(ev)
    out = []
    if drops:
        e = drops[0]
        out.append(_f("oil-pressure-margin", "oil_pressure_drop", "fault", f"Oil pressure fell to {e['to_kpa']} kPa at {e['rpm']} rpm ({e['t']} s, {e['context']}) against about {e['expected_kpa']} kPa normally seen at that rpm, for {e['s']:g} s." +
                      (" Low pressure while braking or cornering is usually oil surge (sump baffling or level), but at this rpm it still costs bearings." if e["context"] == "braking" else "") + " Investigate before any further load work.", events=drops[:10]))
    if dips:
        loaded = sum(1 for e in dips if e["context"] == "under load")
        out.append(_f("oil-surge", "oil_pressure_dips", "warning", f"{len(dips)} short oil pressure dips above {d['oil_min_rpm']:g} rpm that recover within {d['oil_recover_s']:g} s ({loaded} under load). Brief dips that line up with cornering, braking or launches are oil surge (sump and baffling); without acceleration channels the log cannot confirm that.", events=dips[:10]))
    if not out: out.append(_f("oil-pressure-margin", "oil_pressure_steady", "info", f"No oil pressure dips of more than {d['oil_dip_frac']:.0%} above {d['oil_min_rpm']:g} rpm."))
    return out

REGISTRY = [
    ("map_baro_key_on", map_baro_key_on), ("cold_soak_agreement", cold_soak_agreement), ("tps_endpoints", tps_endpoints),
    ("trigger_integrity", trigger_integrity), ("ethanol_plausibility", ethanol_plausibility), ("lean_events", lean_events),
    ("cl_trim_saturation", cl_trim_saturation), ("cl_masking", cl_masking), ("iat_compensation_slope", iat_compensation_slope),
    ("hidden_coolant_trim", hidden_coolant_trim), ("fuel_pressure_tracking", fuel_pressure_tracking), ("duty_lambda_departure", duty_lambda_departure),
    ("load_axis_saturation", load_axis_saturation), ("ignition_load_monotonicity", ignition_load_monotonicity),
    ("knock_noise_vs_load", knock_noise_vs_load), ("knock_repeatability", knock_repeatability), ("pull_conditions", pull_conditions),
    ("oil_pressure_dips", oil_pressure_dips),
]

def scan(log, tables=None, profile=None, only=None, d=DIAG):
    """Run every diagnostic that the log supports. Returns a Result; findings carry their test's id in `diagnostic`."""
    r = Result("diagnostics-scan"); c = Ctx(log, tables, profile, d)
    skipped = {}
    for name, fn in REGISTRY:
        if only and name not in only: continue
        try: r.findings.extend(fn(c))
        except Skip as s: skipped[name] = str(s)
    r.gate_summary = gates.summary(c.reasons)
    if skipped: r.notes.append("Not checked: " + "; ".join(f"{k} ({v})" for k, v in skipped.items()) + ".")
    r.notes.append("Diagnostics report likely causes only; they never propose table changes. Thresholds are listed in tools/analysis/diagnostics.py.")
    return r
