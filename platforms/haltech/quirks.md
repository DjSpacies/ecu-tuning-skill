---
id: platforms/haltech/quirks
title: Haltech quirks
layer: L3
confidence: medium
sources: [vendor-documentation, practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/haltech/semantics]
supersedes: []
---

# Haltech quirks

Tags: `vendor-doc` (Elite Series help, ESP 2.59.3) and the training source ids `practice`, `practice`,
`practice` for behaviour seen by tuners on Platinum Pro, Elite (ESP and NSP software) and Nexus units. What
settings mean is in `semantics.md`; this file is about how the product actually behaves, the traps it sets and the
workarounds tuners use. The adapter has not yet met a real Haltech file, so none of this is sample-observed.

## Claim

Most Haltech surprises come from a handful of behaviours: corrections applied twice (auto air-temperature
compensation plus a populated IAT table); closed-loop and long-term trims that hide base-table error while lambda sits
on target; auto-tune functions (Quick Tune, trace) that assume the error belongs to one centred cell; idle and DBW
controllers pinned at a configured authority limit; parameter names that do not say what they do (accel deadband,
closed-loop delay, limiter adder); laptop logs too slow for transients; and defaults some tuners consider wrong (cut
method, EGT limit). Check for these before diagnosing the engine.

## Why (derivation)

- Every closed-loop controller (fuel, idle, boost) reaches its target by adding its own output. A target that is met
  says nothing about the base table; the size of the trim, integral or learned value does. Haltech exposes those
  outputs as channels, so the test is always available.
- The VE model already corrects for air density through the gas law; an extra IAT table that is also density-shaped
  repeats it.
- Auto-correction tools compare measured lambda with target in the active cell. When the operating point sits between
  breakpoints the ECU interpolates, so the measured error belongs to a blend of cells and correcting one does not fix it.
- Idle base values are percentages of a configured maximum (see `semantics.md`), so a maximum set too low caps the
  controller however much it asks for.
- The laptop link samples at a few hertz, far slower than a transient lambda event.

## Assumptions

- Elite on ESP 2.59.3 for `vendor-doc` facts; training sessions recorded on various Platinum Pro, Elite ESP, Elite NSP
  and Nexus firmware. Some behaviour (ESP connect time, conversion faults) may have changed in later releases.
- Defaults as shipped; a dealer base map may differ.

## Breaks when

- ESP and NSP name and lay out parameters differently; a trap on one may not exist on the other.
- Numbers quoted below come from particular cars in the sessions (a stock VQ35 350Z, a 4G63 Evo 9, a Subaru STI, a
  turbo VQ35); they are examples, not limits.
- Several observations are one practitioner's experience on one car and are labelled as such.

## Practical use

### Software, connection and logging
- `vendor-doc`: changing the Tuning Method changes the meaning of every Fuel Base value.
- PC-link logging runs at roughly 2-4 Hz in the Elite session, so live time graphs smear fast transients. Judge
  acceleration enrichment, predicted MAP and tip-in lambda from the internal ECU log at a higher rate
  (`practice` 233).
- Log playback shows which cell of each table was active at every instant, with measured lambda and trims, so ramp-run
  corrections can be read cell by cell; on the Platinum Pro the same playback shows which cells of both accel tables
  fired (`practice` 048, 054).
- ESP took about a minute to connect in the session, against a few seconds on NSP; at a track that can decide whether a
  pit-lane change is possible (`practice` 301).
- ESP to NSP conversion: in one session the tools-menu convert failed at the last step and NSP looped without
  connecting. The workaround shown was to update ESP to its final release first and, if conversion still fails, roll
  back to the pre-NSP firmware and update through the online prompt (`practice` 301).
- NSP has a trigger scope that shows the raw trigger voltage beside the ECU's interpreted tooth state, and the same for
  the home input; a triggered capture can freeze a fault for support. On a fresh install a no-start is most often a
  trigger setup fault, so start there (`practice` 301).
- The NSP course unit had no output test mode. The workaround: confirm fuel pump prime by powering down fully and
  keying on, test fans by temporarily editing duty or thresholds, and continuity-check every injector and coil output
  to its cylinder (`practice` 8.60).
- Nexus: with a sensor open circuit on the bench the ECU substituted a default coolant temperature because the voltage
  was outside a hidden sanity window; an implausible reading may be a fault substitution, not the sensor
  (`practice` 321).
- CAN: Haltech broadcasts a fixed stream, so pairing with a configurable device (a PDM, a dash) means doing the mapping
  on the other device (`practice` 182). A TCU emulating Haltech CAN IO expanders updated at a nominal 10 Hz, closer
  to 5 Hz in logs, too slow for paddle shift requests; those were hardwired instead (`practice` 413). Replacing a
  factory ECU (350Z in the session) can lose cluster and fan control that the factory ECU sent over CAN; the fix shown
  was to rebuild those messages from another device (`practice` 102).
- A Mainline dyno can send torque and power to the Elite over CAN so they show on the tuning laptop and are logged with
  ECU data (`practice` 115).

### Fuel model traps
- Double air-temperature correction: with Auto V.E. Air Temp Compensation on, a populated IAT fuel table corrects
  density twice and lambda drifts with IAT. Start that table at zero and use it only for small residual corrections,
  for example adding fuel back at high IAT and low load where the model pulls too much (`practice` 8.72;
  `practice` 074, 165). The course software lesson describes no manual table with auto off, while other sessions
  turn auto off and hand-tune a manual IAT table; check what the loaded software version offers.
- Injection Time mode: the table number excludes dead time. In the session the table read about 0.57 ms at idle while
  the delivered pulse was about 1.75 ms; oversized injectors on a mild engine make the table numbers very small
  (`practice` 071).
- Injector data formats: one injector maker's Haltech drop-in data gave the short pulse adder in percent, which did not
  match the NSP table's units. The practitioner used the same injector's data formatted for another ECU (in ms) and
  rebuilt the axis to suit before pasting (`practice` 407). Check units before pasting any supplier file.
- Injector drive: the Evo 9 uses low-impedance injectors through a factory ballast resistor pack, so the ECU is set to
  high impedance (saturated) despite the injectors; check for a resistor pack before choosing drive mode
  (`practice` 407).
- Platinum MAF mode: the correction table never ends up flat at 1.0. The residual comes from the MAF calibration no
  longer matching a changed intake (filter, airbox, especially tube diameter) and from unmodelled injector
  non-linearity at short pulses, which the low-pulse-width region carries (`practice` MAF/ms/VE session).
- VE values near 200 point to wrong injector flow or wrong engine capacity, not to dead time, which mostly affects
  short pulses (one practitioner's diagnosis, `practice` M1 VE session).
- Baro is not corrected automatically; on a speed-density or alpha-N car that changes altitude, the baro table must be
  enabled and tuned (`practice` 241).
- Alpha-N into boost: where a hard-pushed turbo on a TPS-based VE table drifts rich at high boost and rpm, the session
  removed fuel only there with a MAP-by-rpm fuel correction (a few percent, up to about 8 % at 200 kPa high rpm),
  leaving the base table alone (`practice` 089).

### Closed loop, learning and auto-tune
- Lambda on target does not mean the base cell is right. Long-term trim slowly absorbs short-term trim until
  short-term reads near zero while the learned table does the work (`practice` 165). After the tuner corrects the
  base table, the existing trim keeps applying until it unwinds, so mixture goes briefly the other way (Platinum,
  `practice` MAF/ms/VE session). Read base error as measured error plus all active trims.
- Bank allocation: if one bank trims to its rich limit while the other trims to its lean limit and both wander, the
  widebands are assigned to the wrong banks; each bank is being corrected by the other's sensor (`practice` 063,
  182).
- Applying dual-bank learned trims does not zero them: the average goes to the base table and each bank keeps half the
  difference (see `semantics.md`).
- Learning windows: if long-term trim runs during warm-up, post-start or hot restart it learns the compensation
  tables' error. Sessions set a minimum coolant temperature for learning (about 60 C in one, normal operating
  temperature in another), lock it out during post-start and coolant correction, and fix warm-up error in its own
  tables (`practice` 063, 358). One practitioner sees no reason to block short-term trim when cold, as it tracks
  targets well during warm-up (`practice` 358).
- Long-term gain: in one practitioner's tests the maximum gain learned fast without oscillating, while a small gain was
  too slow to be useful (`practice` 063). The NSP session left the default gain.
- Rich bias makes the learned table sit richer than target; it is an optional hedge (2-5 % in one session) against a
  wideband fault, and should be zero to learn the true target (`practice` 063, 358).
- The NSP closed-loop delay table is a re-engagement delay after events such as overrun cut, not transport delay; leave
  it near default unless trims chase fuel-cut recovery (`practice` 358). If closed loop is active during overrun,
  the sensor reads full lean and the loop winds up to its limit, giving a rich hit on tip-in and then a lean swing;
  standalones often need this lockout configured where factory ECUs block it (`practice` EFI Advanced part 35).
- Quick Tune: each correction is limited to about 30 %; one key corrects only the current cell, another also pushes the
  change into the next load and rpm cells (`practice` 301). One press can overshoot (in one demo from -6 % to
  +1-2 %); off-centre operation, heat soak or abnormal IAT and coolant skew it. Hold the engine centred in the cell,
  disable long-term trim, and repeat until short-term trim reads zero (`practice` 8.66; `practice` 301, 358).
  A free-rev demo did not land in one shot because the engine was not centred.
- Trace mode averages about 2 s of lambda per visited cell and folds closed-loop trim into its proposed correction, so
  it works with closed loop on; only cells with data change. Cells crossed quickly or clipped at a corner give
  unreliable numbers (one cell in the session suggested 9 %) and should be excluded or hand-tuned; rough throttle
  triggers transient enrichment and spoils the averages (`practice` 8.69; `practice` 358).
- Self-learning from a flat table: a manufacturer anecdote reports a car becoming roughly tuned after a long drive on
  a flat table; the practitioner stresses this does not replace tuning (`practice` 063).

### Idle and drive-by-wire
- Idle authority limit: if a cold engine idles low with the idle controller at 100 % of its range, the configured
  maximum DBW idle position is too small. Sessions start near 10 % throttle and raise it a few percent at a time;
  typical ranges are 8-10 % but some engines need 12-15 %. Too large a range coarsens resolution and can make idle hunt
  (`practice` 117, 138, 207, 390). One E85 car would only start cold with pedal held for a minute; the practitioner
  read that as too small an idle range, although vendor support had reportedly told the owner it was normal.
- Headroom rule from one practitioner: size the maximum so the worst case (usually cold start) still leaves about 25 %
  of range in reserve (`practice` 117).
- Base table hidden by integral: idle can sit exactly on target with the integral output at -6 %, meaning the base
  value is about 6 % too high. Correct the base by the integral and proportional outputs until they sit near zero, or
  zero the PID gains to force open loop. Selecting the open-loop idle mode instead hides the target table in that
  software (`practice` 117). The NSP course verified the idle circuit by switching to open loop and stepping the
  base table (`practice` 8.65).
- Raw gains: Haltech idle PID gains are raw values much larger than MoTeC or Link equivalents, and unitless gains make
  it hard to reason about each term (`practice` 105, 117). The session's method: start from defaults, double until
  oscillation, then halve.
- DBW sensors belong on the recommended high-speed inputs (AVI 2-5), which are tied to the supervisor processor
  (`practice` 138). A DBW fault and pedal calibration error at full throttle straight after a calibration run was
  cured by repeating both calibrations until the ECU reported them good.
- Open-loop boost control drives the solenoid at whatever duty the table holds, so it ticks at idle; set off-boost
  cells to 0 % (`practice` 211).

### Transient fuel
- The Elite parameter called load acceleration deadband is really the decay rate: smaller holds enrichment longer. If
  lambda heads toward target after a stab and then leans again before steady fuelling takes over, enrichment is being
  removed too early; halve that value (`practice` 233).
- The Elite default enrich amount table rises with rpm, which looks backwards against physics; it is a pseudo-VE term,
  so with a correct VE table the session scaled the whole table rather than reshaping it.
- Random rich blips at steady throttle, especially on older engines, can be a noisy worn TPS crossing a too-sensitive
  rate threshold and firing accel enrichment. Log the enrichment channel; widen the threshold if it fires without a
  real throttle change (`practice` 233). The NSP equivalent is predicted MAP engaging on throttle noise: check the
  TPS rate channel and set sensitivity so prediction fires only on real movement (`practice` 348).
- Predicted MAP time too short reverts to live MAP before it catches up; too long on a turbo engine holds about
  atmospheric while boost builds, causing a lean condition. The session started from the 200 ms default and moved in
  large steps (halve or double) before refining (`practice` 348).
- Platinum Pro async enrichment has a lockout delay so repeated blips do not stack async fuel; the presenter recalled a
  hard cap on the async pulse, with any excess moved to synchronous pulses (`practice` 048).

### Limiters, protection, launch
- Haltech defaults the main limiter cut to ignition; one practitioner considers that the wrong default given valvetrain
  risk and uses injection cut with soft cut type (`practice` 374).
- Combined cut modes apply the second method 100 rpm above end rpm, so the engine can exceed the set limit by up to
  100 rpm; this matters only if the limit sits at the mechanical limit.
- Cut events logged while displayed rpm is below the limit are normal: soft cut acts on the raw per-tooth rpm, which is
  faster and unfiltered compared with logged rpm.
- The cut-off mode adder behaves as a randomiser: lower is rougher, higher smoother, but near the top of its range it
  turns rough again; the session starts around 50.
- A cold rev limit (reduced below about 20 C in one session) will be reported by customers as misfiring until warm;
  tell them (`practice` 374).
- The NSP default EGT protection value is far too high in one practitioner's view; he uses a much lower pump-fuel turbo
  value and a per-cylinder threshold where individual EGTs are fitted (`practice` 372).
- Severe protection levels that kill power suddenly can be dangerous in competition (a following car, a driver holding
  a slide on throttle); sessions reserve them for faults that truly threaten the engine and use milder tiers
  (enrichment, boost reduction, retard, moderate limit) for the rest (`practice` 253, 372).
- Remember to lift conservative first-start limits (rev limit, overboost cut) before ramp runs, or the runs hit them
  (`practice` 8.68).
- Platinum launch timing table is absolute, not an offset; tuners coming from overlay-style ECUs must fill it with full
  timing values. A heavily retarded launch map makes the engine lethargic; the session used a throttle threshold before
  switching to it and retarded only the 90-100 % throttle cells. A very narrow soft-cut range gave erratic, harsh rpm
  control, a wide one smooth control, and the range also shifts where rpm settles (`practice` Platinum Pro launch
  session).

### Ignition, triggers and knock
- Timing lock overrides the table and all compensations. Lock at an angle the engine runs happily with a visible mark,
  set the TDC angle roughly while cranking with injectors disabled, then again once running; step the offset while
  watching which way the mark moves. If the mark wanders at idle (low tooth count, big cams), raise idle so it
  stabilises (`practice` 8.75; `practice` 176).
- Keep sync set to always use the home signal: an ECU that ignores it after first sync cannot recover from lost teeth
  (`practice` 8.61).
- Ignition edge: nearly all coils fire on a falling edge, some MSD, Ford and Honda systems rising; the wrong edge can
  destroy coils, so keep coils unplugged during configuration (`practice` 8.60, 8.72; `practice` 208).
- Knock threshold method shown: set the threshold to maximum, make a no-knock ramp run confirmed by ear, set each rpm
  breakpoint about 10 % above the no-knock peaks, and confirm with another clean run. Centre frequency was found with a
  spectrogram while inducing brief light knock at low rpm (`practice` 057).
- Long-term knock trim is reactive: it needs knock to happen first, so it is a field backstop for bad fuel, not a way
  to tune timing (`practice` 063).
- Platinum cam control: overshoot was limited with duty clamps, a tight dead band and a coolant lockout because cold oil
  gives poor control (`practice` Platinum cam session).

### Cold start
- Post-start enrichment and coolant correction are active together and add. Coolant temperature barely moves while
  post-start decays, so lambda error after post-start has gone, at the same coolant cell, belongs to the coolant
  correction alone (`practice` 205, 390).
- The post-start table also serves hot restarts; lean seconds after a heat-soaked restart are fixed in its
  high-coolant rows. Make its last time column zero so enrichment does not persist.
- Prime and cranking cannot be judged on a wideband; judge by how crisply the engine fires. Isolating cranking by
  disabling coolant and post-start corrections makes the engine fire and then die, which is expected.

## Worked example

Elite, idle closed loop on. Warm idle sits on its 800 rpm target with base table 48 % and the idle integral output
logged at -6 %. Reading: the controller is removing about 6 % of opening, so the base is about 6 points high. Change
the base to 42 %. Idle first dips, because the integral is still pulling 6 %, then recovers as the integral unwinds to
zero. Final check: integral and proportional near zero at target, and a throttle blip drops straight onto target. In
the session that last step needed a decel offset of a few percent with a decay of about 1.5 s; with none, rpm dipped
toward 650 before recovering, and with too much it hung near 1400 (`practice` 117).

## Disputed / conflicts

- Limiter cut method: the shipped default is ignition cut; one practitioner prefers injection soft cut for valvetrain
  reasons (`practice` 374). Haltech's reason for the default is not recorded.
- EGT protection default: one practitioner's view that the default is far too high (`practice` 372). Test: compare
  the default against the turbine maker's rating for the fitted turbo.
- Warm-up in post-start only (Haltech guidance) versus coolant 3D table plus post-start bridge (one practitioner); see
  `semantics.md`.
- DBW idle range: vendor support reportedly called a pedal-assisted cold start normal on one E85 car; the practitioner
  attributed it to too small an idle range (`practice` 390). Test: log idle output at cold start; pinned at 100 %
  means authority, not fuelling.
- Short-term trim when cold: one practitioner would leave it on during warm-up (`practice` 358); other sessions set a
  coolant minimum on trims in general (`practice` 063). All agree long-term learning should be blocked during
  warm-up.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
