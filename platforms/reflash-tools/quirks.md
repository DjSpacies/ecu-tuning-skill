---
id: platforms/reflash-tools/quirks
title: Factory ECU reflash quirks
layer: L3
confidence: medium
sources: [practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/reflash-tools/semantics]
supersedes: []
---

# Factory ECU reflash quirks

Behaviour of factory ECUs and the tools used to reflash them, as seen by tuners in the training sources (`practice`,
`practice`, `practice`). Organised by tool: cross-tool factory ECU behaviour first, then HP Tuners (GM and
Dodge), EcuTek (Subaru and Toyota 86), Hondata, the open-source tools (EcuFlash, RomRaider) and WinOLS. No COBB
behaviour is recorded from the training sources yet. Vendor rules are in `semantics.md`. Table names and strategies
are specific to each ECU family and version; nothing here carries across families without checking.

## Claim

Reflash tuning differs from standalone tuning in four ways that drive most mistakes: changes are not live, so every
iteration costs a flash, a restart and a disturbed thermal state; factory strategies hide their real output behind
modifiers, adaptations and blended models (high and low octane tables, knock-learned multipliers, MAF blended with a
speed-density model, long-term trims that persist into open loop); the factory closed loop hides calibration error
unless it is disabled; and table definitions, especially community ones, may be incomplete or wrong. A tuner works
around these with histograms on the table's own axes, isolating one subsystem at a time, and verifying definitions.

## Why (derivation)

- Factory ECUs on MAF meter air mass directly and carry fuel tables as target AFR, lambda or equivalence ratio, not pulse
  width; injector models convert fuel mass to time. Load axes are air mass per cylinder or per revolution, so both fuel
  and spark depend on the MAF or VE model being right (`practice` 079, 099; `practice` EFI Fundamentals 5.6;
  `practice` EFI Advanced part 33).
- Because spark tables are indexed by calculated air mass, a wrong airflow model also moves the engine to the wrong
  spark cell: delivered timing is not what the tuner thinks (`practice` 224).
- Closed loop and trims drive measured lambda to target, so a wideband reads almost no error while the model is wrong.
  Long-term trims learn slowly and some stay applied in open loop, so a dyno-tuned full-load mixture can drift days
  later (`practice` 199, 215; LS3 full-power session).
- The factory calibration was developed for one engine with large resources, so cold start, idle, idle-ups and part
  throttle usually stay valid after light modifications; the work concentrates on open-loop full load
  (`practice` 179; `practice` EFI Fundamentals 9.1).

## Assumptions

- Training sessions cover GM Gen 3/Gen 4 and E38 PCMs, a late Dodge with a neural-network airflow model, Subaru and
  Toyota 86 ECUs, Mitsubishi Evo, Honda, and Bosch MED9 binaries. Software versions are not stated.
- Numbers below are practitioner examples on particular cars, not limits.

## Breaks when

- Different ECU generations of the same maker use different strategies (early LS1 real VE table versus later virtual
  VE coefficients; flash write times from tens of seconds to many minutes).
- Commercial vendors add tables over time; a missing table in one version may exist in another.
- Heavily modified engines (big cams, forced induction added) invalidate the assumption that idle and part throttle
  can be left alone.

## Practical use

### Cross-tool: factory ECU behaviour
- Scope: for mild bolt-ons a basic reflash is about an hour or two, concentrated on full-load open loop; bigger
  injectors, cams or added boost widen it greatly (`practice` reflashing basics). On modern cars, replacing the
  ECU breaks modules that depend on its network messages (trans shifting, A/C, cluster), which is why reflash dominates
  (`practice` 179; `practice` EFI Fundamentals 9.1).
- Closed-loop health check: on a near-stock car, combined trims at idle and cruise within a few percent mean the
  closed-loop area can be left; trims well beyond about 5 % on the road after an intake change mean the MAF curve needs
  rescaling; 10 % or more means it definitely does (`practice` 079, 204, 364). Even a near-stock Dodge with only
  mufflers changed showed trims around 15 %.
- A brief short-term trim spike on tip-in (about +10 %, settling to a few percent) is normal factory closed-loop
  behaviour; tuning it flat can make the car worse to drive (one practitioner, `practice` 046).
- Factory trim authority is typically about ±25 % before a rich or lean code; one practitioner limits a well-tuned
  engine to about ±10-15 %, not tighter, so hot-restart heat soak can still be corrected (`practice` 199).
- Long-term trims: one practitioner often disables them on modified cars so full-load fuelling is exactly what was
  programmed, because factory long-term trims learn over a few broad zones and can stay applied at full load; others
  leave them on (`practice` 199, altitude session, M1 closed-loop session; LS3 full-power session).
- Flash discipline: each flash forces a shut-down and restart; after a hot restart short-term trim sat 6-8 % rich of
  its settled value, so the next pull is not comparable until the engine is stabilised again (LS3 full-power session).
  Secure power and cable before every flash: an interrupted flash can brick some ECUs, Subaru in particular
  (`practice` reflashing basics).
- Batch versus one change: slow flashing tempts batching many edits, which hides which change did what; one practitioner
  keeps standalone discipline (fuel first, then timing in small steps); another notes that long flash times push you to
  plan changes in batches (`practice` reflashing basics, 184).
- Logging bandwidth over the diagnostic port is limited; every extra parameter lowers the sample rate, so build
  task-specific lists (fuel, ignition, cam, boost) (`practice` 247, reflashing basics).
- Base timing on factory trigger hardware is inherently right and there is usually no timing-lock mode; a timing light
  just shows the moving advance (`practice` 176).
- High and low octane tables: many factory calibrations blend toward a low-octane ignition (and sometimes richer fuel)
  table as knock accumulates; account for both when reflashing (`practice` EFI Fundamentals 5.6).
- Factory knock detection: on stock to moderate GM engines one practitioner mostly trusts it; on modified engines factory
  systems have both reported false knock (safe, costs power) and missed audible knock (dangerous). Validate by briefly
  over-advancing one light-load, low-rpm cell, moving in and out of it, and confirming the logged knock matches what is
  heard on headphones (`practice` 083, 152, 179; `practice` EFI Fundamentals 8.3). Several Evos logged zero
  knock while knock was audible (`practice` reflashing basics). Knock counted on a harsh rev limiter is usually
  block shake, not combustion knock; check by ear (`practice` 084).
- Factory widebands are built for near-stoich control: one Toyota 86 sensor read about 0.83 when the dyno read 0.90, a
  Subaru front sensor read 0.2-0.3 AFR rich at full-load mixtures. Compare against a trusted wideband before use
  (`practice` EFI Fundamentals 4.6; `practice` 247, M1 closed-loop session). A factory narrowband input cannot
  be recalibrated into a wideband; use a controller with narrowband simulation if the bung must be shared
  (`practice` 126).
- Injector swaps: GM and Ford model injectors fully (flow against differential pressure, offset against voltage and
  pressure, short-pulse adder below a limit; Ford uses low and high slopes about a breakpoint). With supplier data for
  that ECU and tool, AFR can be essentially unchanged after the swap; without it, hours go into fighting idle and errors
  get masked elsewhere. Buy injectors with plug-in data for the specific ECU (`practice` 243, injector
  characterisation session; `practice` EFI Fundamentals 6.5). On ECUs with only a flow scalar and an offset table:
  scale by the flow ratio to start, adjust the scalar at light cruise (long pulses) until trims are near zero, then
  idle (short pulses, latency), and iterate; a too-small dead time shows as a lean idle (`practice` 087, 147). With
  no short-pulse data, keeping stock or zeroed values both leave some error, mostly absorbed by closed loop at idle
  (one practitioner, `practice` Link G4 injector session).
- Older factory ECUs drive low-impedance injectors through a ballast resistor pack on a saturated driver; keep the pack
  for low-Z replacements and remove it for high-Z ones (`practice` EFI Fundamentals 4.11).
- MAF cars and blow-off valves: venting already-metered air (atmospheric BOV, or reversion back past the MAF) gives a
  rich spike that can stall the car on shifts or when stopping; recirculating valves and longer tube between MAF and
  turbo avoid it (`practice` 207, 209).
- DBW: some makers detune a cheaper model of the same engine only by limiting throttle opening, and many factory DBW
  maps close the throttle near the stock limiter, so a raised limit still stops making power at the old one; edit the
  pedal-to-throttle mapping (`practice` 155, 178, reflashing basics).
- DTCs: late-model cars can set a code even for a larger exhaust; disable codes the modification will legitimately
  trigger. Ignition-cut launch on an 86/BRZ sets genuine misfire codes; disabling them also hides real misfires
  (`practice` 084, reflashing basics). VVT engines with modified cams can trip cam error faults because factory
  limits on cam target-versus-actual error are strict (`practice` 113).
- Outputs: some tools allow output reassignment; reusing the evap purge output for a boost solenoid is a common trick
  on NA cars turbocharged on the factory ECU (`practice` EFI Fundamentals 4.12).
- Factory MAP sensors cap boost (the STI throttle-body sensor reads to about 1.6 bar boost); fit a higher-range sensor
  and keep headroom (`practice` Practical Standalone Tuning 8.112).
- Automatic cars on the dyno: kickdown from a settled gear ruins runs and can cause wheelspin; fix the gear first. Dips
  in a stock auto car's curve were knock retard, not the transmission. Low-rpm full load is rarely used on the road
  because the box kicks down, so effort goes higher in the rev range (`practice` 100).
- Direct injection: factory maps raise rail pressure and advance start of injection at high load and rpm. An FA20 map
  that appears to inject during the exhaust stroke at high rpm really delivers after TDC once opening latency is
  counted; optimisation gains there were confirmed on several ECUs (`practice` 157).
- Factory cold start runs lambda 1 early for catalyst light-off, relying on fast closed loop; heavily cammed engines may
  want richer cold and even hot idle (`practice` M1 cold-start session). Factory stoich at idle and cruise is an
  emissions choice, not best economy; a slightly lean cruise is possible only where emissions compliance does not apply
  (`practice` 150; `practice` EFI Fundamentals 2.11).
- After big cam changes, steady-state methods (left-foot braking on the road) may still be needed to recalibrate the
  MAF or VE model (`practice` left-foot braking session).

### HP Tuners (GM)
- Strategy: closed loop at stoich until a power-enrichment (PE) enable threshold of throttle against rpm is crossed;
  the threshold falls with rpm (in one stock calibration from 100 % below about 1600 rpm to about a quarter of travel
  near 6000). PE targets are a 2D table of equivalence ratio against rpm (separate gasoline and alcohol tables).
  Equivalence ratio is the reciprocal of lambda; GM uses 14.67 as gasoline stoich in its flex-fuel table
  (`practice` 065, 079, 179, 224; LS3 full-power session).
- Delivered spark is not the base high or low octane table; several modifiers apply. Log delivered spark into a
  histogram to see real timing per cell (`practice` 215).
- MAF plus speed-density blend: the ECM leans on a speed-density path during sharp transients (real VE table on early
  LS1, coefficient-based virtual VE on later ECMs). Calibrate each with the other disabled: for MAF work set the dynamic
  airflow high-rpm disable and re-enable very low so only the MAF is used; for speed density fail the MAF
  (`practice` 099, 199, 204, 224).
- Preparing for MAF calibration (one demonstrated list): disable closed loop and long-term trims by raising their
  coolant enables beyond reach; set open-loop modifier tables (including alcohol) to 1.0; disable catalyst over-temp
  enrichment and decel fuel cut; set PE to one fixed target and raise its threshold; save the stock read first and
  copy every changed table back with compare afterwards (`practice` 099, 204).
- Histograms are the reflash substitute for live tuning: copy the target table's exact breakpoints into the histogram
  axes (MAF frequency, MAP by rpm, air mass by rpm, coolant), log equivalence-ratio error (two decimals) and paste
  back with multiply-by-percent. If AFR error is chosen while logging in other units the histogram stays empty
  (`practice` 179, 199, 204, 215, 224, 292).
- Histogram cells show the average of samples; check the hit count layer and last-value view. Thresholds used by the
  practitioners range from about 200 hits per cell to about 5000 at cruise; isolated outliers and alternating signs
  between neighbours mean bad data, and errors near 1 % are within run-to-run noise (`practice` 080, 099, 199,
  215).
- Paste special only changes visited cells and pastes bad data faithfully; use full correction on the first pass, the
  half-error option after, then smooth and hand-blend unvisited cells along the neighbouring trend. Two or three
  iterations are typical (`practice` 099, 204, 215, 292).
- The stoich-to-PE transition logs a false lean error (3 % up to 15 % in the sessions) because measured lambda lags the
  stepped target. Collect steady-state data below the PE threshold and full-PE ramp data separately; discard
  transition cells (`practice` 204, 215).
- A good MAF curve is smooth and roughly exponential; bumps cause driveability faults. One practitioner corrects small
  full-load errors (within about 2-3 %) in the commanded PE table and larger ones in MAF scaling, noting GM itself
  leaves small offsets in PE rather than distort the curve (LS3 full-power session). After skewing PE to correct an
  error, the logged commanded value no longer equals desired lambda, so the error channel still reads the old error;
  judge against the real desired lambda.
- Speed density patch: apply, save under a new name, reopen, then a full write (not calibration only) once. The patch
  silently resets MAP scaling to a 2-bar sensor (copy the original back if the 1-bar sensor stays); new VE tables are
  zero-filled so the engine cranks without firing; GM VE units run into the thousands but scale linearly; keep the
  runner-open, runner-closed and cylinder-deactivation VE tables identical. The ECU only falls back to SD when it
  considers the MAF failed, so set MAF codes to report the error without a lamp, not to no-error (`practice` 224).
- On a MAF car one practitioner keeps a genuinely lower low-octane table, since the ECU biases toward it as knock
  accumulates, a predictive margin knock retard alone lacks; on speed density, which loses that adaptation, he copies
  high into low. Many tuners copy high to low regardless (`practice` 224).
- MAF deletion: removing the small early LS1 MAF gained real power; on a later L98 the difference was within run-to-run
  noise. Switch to SD only when the MAF is proven restrictive, a big-overlap cam pulses reversion through it, or the
  engine is boosted (`practice` 224).
- Idle: base running airflow is the feed-forward airflow for idle throttle. Big cams need much more of it (an initial
  rise of 50 % or more in one session); build it from a histogram of airflow against coolant during a cold-to-hot idle
  and add a little surplus so rpm does not dip on return to idle (`practice` 215, 217). If a big-cam engine will
  not hold cold idle however much airflow is added and logged throttle flatlines, raise the ETC idle maximum
  effective area a little at a time; drilling the throttle blade is the wrong fix (`practice` 207, 217).
- Adaptive idle spark adders (over and under speed, by rpm error, separate park/neutral and in-gear) are tuned for a
  smooth stock cam and are too aggressive with a lopey cam; one session halved them. The same tables, made far more
  aggressive in park/neutral only, create a cosmetic lumpy idle (`practice` 184, 217).
- Bi-directional scanner functions (ECM dependent) can set idle, force closed loop, reset long-term trims, kill
  injectors and lock gears; reset trims after calibration changes (`practice` 190).
- Read and record DTCs before clearing; a code after a hardware change may be a diagnostic that needs its error mode
  changed (`practice` 190). LS swaps: the immobiliser option sits at operating-system level, so it needs a full
  write (`practice` 190). The gear and tyre wizard rescales speed and shift scheduling together.
- Flash times: about 40-45 s for a calibration write on an E38 (skip the TCM write), several minutes for a full write
  (`practice` 080, 184, 224). Most current GM PCMs cannot be live tuned.
- PE changes for response: one stock E38 calibration delayed PE until 60 % pedal below 2500 rpm; lowering it (to 45 %
  in the session) and raising the PE ramp rate made part-throttle acceleration crisper, without letting light cruise
  enter PE (`practice` LS3 full-power session).
- Unexplained rich running for ten minutes or more after a flash on a late LS was a hidden modelled parameter
  (injector tip temperature) missing from the definition until the vendor exposed it (`practice` 126).
- Fan control in the stock calibration reaches full fan only above about 103 C; one practitioner brings it earlier with a
  cooler thermostat on knock-limited engines (`practice` 190).
- Wideband into the scanner: analog inputs suffer ground and voltage offset; a serial feed is preferred. With an analog
  input, command the controller to fixed low and high outputs, read what the logger sees, and fit a two-point transform
  instead of the canned one. An Innovate LM2 works only through its serial output, and the programmer software may
  need opening and closing before recording so the port is found (`practice` 179, 190, 199, 219).
- No GM patch provides aftermarket electronic boost control, to one practitioner's knowledge (`practice` 190).

### HP Tuners (Dodge)
- The late Dodge airflow model is a neural network; before a trainer existed, tuners fudged the injector pulse-width
  table, which hides airflow error in injector data. The trainer exposes VE tables per intake and exhaust cam
  position; on a cam-in-block engine only the diagonal combinations occur. Expect two to four retrain iterations
  (`practice` 364).
- Histograms per cam table use cam-centreline filters about 10 degrees wide; approximate, but worked in practice.
- Targets are fuel/air ratio with PE as an additive offset: target AFR in PE equals 1 / (0.068 + table value). The
  stock full-load target on an NA Challenger (about 11.9:1) was richer than needed.

### EcuTek (Subaru, Toyota 86)
- Total Subaru timing is base table plus (knock-learned advance multiplier, 0-1) times advance table; the advance table
  is an adder, which is why it looks implausibly low. Three tables matter: base with VVT on, base with VVT off (used
  when cam phasing sits at zero, for a while after a flash) and advance. Load is grams of air per revolution
  (`practice` 088, reflashing basics).
- After a flash or reset the advance multiplier restarts around 0.7 and climbs only under knock-free load; a pull before
  it recovers runs short of timing, so a change can look ineffective. Bring it to 1.0 before comparison pulls and watch
  it throughout. On turbo Subarus jagged torque from constant multiplier activity was cured by a knock-free base table
  and a reduced, smoothed adder.
- The effective ignition view combines base and advance with a slider for the multiplier; check the final map is
  smooth.
- Fuel is a target-AFR table on g/rev; correcting it runs inverse to a fuel-quantity table (raise the number to remove
  fuel). Do not type desired values and skip the wideband.
- Converting a MAF car to speed density when each flash takes about two minutes: a hybrid keeps MAF to a load and
  switches above it, shrinking the SD area to calibrate.
- The factory 86 limiter had about 400 rpm hysteresis, feeling like the key was switched off on track; shrinking it
  gave a smooth hold.
- Optimising factory cam maps on an NA FA20 gained only a few kW for many dyno hours in one practitioner's experience;
  dual-cam engines can make a genuine lumpy idle through cam targets (`practice` 184).

### Hondata
- Best treated as a reflash system: a daughterboard makes the factory Honda ECU reprogrammable, later versions live
  (`practice` 182).
- Honda switched-cam strategy uses a load-dependent changeover window with separate low-cam and high-cam fuel and spark
  tables selected by actual cam state, so mixture is right wherever changeover happens (`practice` 294).

### Open-source tools (EcuFlash, RomRaider)
- The ROM is meaningless without a definition for its exact ROM ID; read the ID and confirm coverage before booking
  dyno time. Coverage is usually much better for US-market variants than JDM ones; community definitions can have
  tables at wrong addresses or doing something other than labelled. Open a few maps and check axes and values are
  smooth and plausible (`practice` 126, 182, 247, reflashing basics).
- EcuFlash reads and writes even when RomRaider is used to edit and log; a Tactrix OpenPort cable and model-specific
  flash connectors are needed (`practice` 247).
- Very large injectors have run stoich at idle on Subaru and Mitsubishi reflashes without a defined minimum pulse
  table, but available tables depend on definition quality (`practice` 251).
- Evo knock sum: one practitioner treats occasional low counts, especially on the first hard pull after cruise, as
  livable on pump fuel and acts on knock that repeats at the same rpm and load; this does not apply to high-boost race
  fuels (`practice` 083).

### WinOLS (raw binaries, Bosch and others)
- Finding maps in a binary is a separate skill from tuning; each maker has its own control philosophy, so learn the
  logic first (`practice` 323, 182).
- The automatic potential-maps search proposed 285 maps on one MED9 file, far more than a stage-one tune needs, while
  possibly missing the needed ones; results are unscaled. Treat it as a hint.
- Bosch axes are often preceded by a small axis-length value; adjust display width until the pattern snaps vertical and
  shift alignment until rows rise smoothly. Some maps share one axis set stored after the maps.
- Scaling factors come from expected content: powers of two, decimal factors or recurring odd factors (an rpm axis
  near 26000 raw with factor 0.25 on MED9). Prefer exact factors from a description file; approximate ones can be about
  1 % off.
- When copying properties to sibling maps, copy axis addresses only if axes are shared, and never the map data source.

## Worked example

GM E38 on MAF, stock LS3 at full load. PE target 1.13 equivalence ratio at 3000 rpm, which is lambda 1 / 1.13 = 0.885,
or 0.885 × 14.67 = 12.98 AFR on gasoline. A pull shows measured lambda within 1-2 % of target except 4-6 % lean below
about 2300 rpm. In the session the low-rpm error was beyond the 2-3 % the practitioner will hide in PE, so it went to MAF
scaling: from the equivalence-ratio error histogram on MAF frequency, a band reading 4 % lean is multiplied by 1.04
(telling the PCM there is more air, so it adds fuel). A cell reading 1 % is left alone. Re-flash, stabilise the engine
after the restart, and pull again; expect two or three iterations (LS3 full-power session; `practice` 099).

## Disputed / conflicts

- Long-term trims on modified cars: one practitioner disables them so full-load fuel is exactly as programmed; other
  tuners leave them on (LS3 full-power session, `practice` 199). Test: log long-term trim in the full-load cells
  over a week of driving.
- Trims as a calibration source: one view is that narrowband trims are reactive, hunt and are blind outside stoich, so
  calibrate only with a wideband and closed loop off; another practitioner calls the dithering objection moot and uses
  trims at part load, aiming at trims near zero (within about ±3 %, reworking beyond about ±5 %) (`practice` 199,
  219). Both agree trims are useless in PE.
- Correcting full-load error in PE versus MAF: small offsets in PE (GM practice per one practitioner) versus correcting
  everything in MAF scaling (other tuners) (LS3 full-power session).
- High into low octane copy on MAF cars: one practitioner against, many tuners for (`practice` 224).
- MAF removal for power: common belief that it always frees power; the sessions show it does on early small-MAF LS1s
  and not on later engines (`practice` 224).
- Batching changes per flash: discipline of one change category at a time versus planning batches because flashes are
  slow (`practice` reflashing basics, 184).

## Citations

- practice: Practitioner training and tuning practice, distilled and cross-checked.
