---
id: platforms/aem-infinity/quirks
title: AEM Infinity quirks
layer: L3
confidence: medium
sources: [practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/aem-infinity/semantics]
supersedes: []
---

# AEM Infinity quirks

How the Infinity (and, where marked, the older AEM Series 1/2) behaves on real cars, as shown in training material,
and the traps it sets. What settings mean is in `semantics.md`. Tags: `practice`, `practice` and
`practice` mark which training source showed the behaviour; nothing here comes from AEM's own help.

## Claim

On the Infinity a handful of product behaviours decide whether a tune or log can be read at face value: closed-loop
trim and the calculated corrected-VE channel are the real measure of VE error, not measured lambda; the MAP filter
is non-linear and an under-filtered MAP moves the table cursor between rows; cam angles are degrees of advance from
the phaser's rest position and the cams stay in failsafe until each bank's sync offset is set; injection timing zero
means 360 degrees before firing TDC; trim limits are one global value; and several useful functions (stoich for an
unlisted blend, fixed I/O pins, sensor failsafe values) work only through workarounds.

## Why (derivation)

- The Infinity is built around a VE model: air mass from displacement, VE and density, fuel from that air mass,
  the lambda target, stoich and the injector characterisation. Anything entered wrongly upstream (capacity,
  injector data, stoich, regulator reference) is absorbed into VE, so the order of setup matters more than on a
  pulse-width ECU.
- Closed loop drives measured lambda onto target, so once it is active lambda reads correct whatever the VE cell
  holds. The size and sign of the trim is then the only record of the error.
- Table lookups follow filtered MAP. Raw MAP carries per-cylinder pulsation, and each wobble that crosses a row
  boundary changes the cell weights, so lambda scatters even when VE is right.
- A cam PID that is asked for an angle the phaser cannot reach keeps integrating error; when the target comes back
  in range the stored integral must unwind before the cam follows.

## Assumptions

- Infinity firmware and InfinityTuner of the era shown in the training (a stock Nissan VQ35 in a 350Z was the main
  demonstration car). AEM base maps for that engine; behaviour on other base maps may differ.
- The Series 1/2 point (time-based Honda tables) is from one short video and concerns the older product line.

## Breaks when

- Later firmware may change filter scaling, trim-limit options or the injection-timing reference; check the help for
  the version in use before relying on these.
- On a pulse-width (time-based) AEM product the VE-model statements do not apply.
- Single-practitioner opinions (closed loop at WOT, VVT failsafe) are marked as such and may not suit every car.

## Practical use

### Reading fuel error on this ECU
- With closed loop active, lambda sitting on target says little. Read the closed-loop trim: in the course a cell
  showed lambda on target while feedback added about 2 to 4 %, meaning the cell was that much lean; raising the VE
  cell until trim reads near zero fixed it. Residual trims of 1 to 2 % are accepted because the engine is never
  perfectly steady (`practice` 8.21, `practice` 037, 109).
- The ECU publishes a live calculated new-VE (corrected VE) channel derived from lambda error. Logging it next to the
  current VE lets a tuner scroll a ramp-run log to each breakpoint and type the suggested value in; it is the same
  ratio correction (measured over target lambda) a tuner would do by hand. Example: measured 0.83 against target
  about 0.88 gave a factor near 0.94 (`practice` 109).
- VE and ignition tables display whole numbers by default although the ECU calculates with decimals. Switch the
  number format to one decimal place so small corrections are visible (`practice` 032, 109).
- Test of the VE model: with closed loop off above about 80 kPa, changing the WOT target from about 0.89 to 0.82 gave
  measured lambda within about 0.01 of the new target with no VE edit. If a target change is not tracked, suspect
  injector data, capacity or stoich, not VE (`practice` 032).

### Where the engine really is in the table
- WOT does not mean the 100 kPa row. In one session intake restriction and low barometric pressure (altitude, cold
  weather) held MAP at about 90 kPa at 6000 rpm, so the engine ran in cells whose target nobody had set. Check
  logged MAP at WOT and set target and VE in the rows actually used (`practice` 032).
- The same session showed MAP jumping between about 90 and 97 kPa at WOT with the cursor bouncing between rows and
  lambda scattering. Raising the MAP filter from 30 to 75 settled it. The Infinity's smoothing factor is non-linear:
  little effect from 0 to about 50, then increasingly strong. Aim for about 1 to 2 kPa residual bounce (more at high
  rpm) and check throttle response afterwards.
- The same non-linear smoothing applies to pressure inputs used for protection. Fuel pressure read very erratic
  unfiltered, but heavy filtering on oil pressure can hide the short dips that show oil surge, so the protection never
  sees them. Use moderate smoothing and confirm the trace still moves (`practice` 039).

### Setup values that silently skew fuel
- Engine capacity is the reference for 100 % VE. Re-enter it after any stroke or bore change; an error scales every
  fuel quantity (`practice` 032).
- Stoich comes from a drop-down of common fuels. For a blend not on the list (E30, E50), the workaround shown is to
  select flex fuel and fill the whole stoich-versus-ethanol table with the one value wanted (`practice` 032).
- With a fuel pressure sensor fitted, enable measured pressure in the fuel model (returnless VQ35: about 400 kPa
  static). Still set regulator reference (atmospheric for returnless, manifold for a referenced return system) and
  static pressure correctly: if the sensor faults, the ECU falls back to them (`practice` 8.15, `practice`
  118).
- Dead time for the same injector differed between the injector maker's data and AEM's own bench data (about 1.08
  against 1.24 ms at 14 V and 60 psi) because driver circuits differ. Pick one consistent data set. On a returnless
  system the dead-time table wants voltage and differential pressure axes (`practice` 118).
- Peak-and-hold tables (open time, hold duty) matter only for low-impedance injectors; for saturated injectors they
  sit at 100 % duty. For an unlisted low-impedance injector, borrow those two tables from a similar listed one and
  edit only flow and offset (`practice` 118).
- Injection timing value zero means 360 degrees before firing TDC, not end of injection at TDC as on most ECUs. Read
  every injection-timing number with that offset (`practice` 118).

### Ignition and trigger checks
- Timing lock ignores the main table and all compensations. Lock at an angle that is easy to see on the pulley
  (10 or 15 degrees in the sessions) and adjust trigger offset (0.1 degree steps) until the light matches. Plug-in
  units may already be at zero offset but are still verified (`practice` 8.18, `practice` 058).
- With timing locked, raise rpm to 3000 to 4000: about one degree of movement is normal; a large shift points to
  reversed VR polarity. Small drift between about 1000 and 6000 rpm is removed with the pickup delay setting. This
  matters most when the trigger is wired directly rather than through a factory harness (`practice` 8.18).
- Before first fire, disable injector and coil outputs and crank: the sync state channel should go to 1 and start
  probability to 100 % once cranking settles. Erratic rpm jumps, not the absolute cranking speed (180 to 190 rpm on
  the VQ35), indicate trigger trouble (`practice` 8.16).

### Cam control
- Cam table values are degrees advanced from the rest (most retarded) position, not cam-card centreline figures. With
  cams at rest (solenoids unplugged, idling), read each bank's measured angle and enter it as that bank's sync offset
  so it reads zero. Until that is valid the ECU stays in cam failsafe and does not control the cams. Do it on plug-in
  units too, because of factory tolerance (`practice` 035, 081).
- Default PID gains let measured cam position oscillate around target; adding derivative (about 0.3) tightened it.
  A wandering cam moves airflow and lambda at steady state, so tune cam tracking before any VE work
  (`practice` 035).
- A target beyond mechanical travel (50 degrees asked, 38 reached on the demo VQ35) winds up the integrator; on
  return to 20 degrees the cam took 1 to 1.5 s to follow. Find the real advance limit early and clamp all targets
  inside it (`practice` 081).
- On this speed-density ECU, advancing a cam that makes the engine go lean means more air is entering. In the demo a
  torque drop after advancing was the lean mixture; once VE was corrected to lambda 1 the advance gained torque.
  Judge cam changes only after restoring target lambda (`practice` 081).

### Closed-loop and protection limits
- Closed-loop trim limits are one global value on the Infinity, not a table by rpm and load. That forces a
  compromise between tight high-load authority and the larger trim (up to about 15 %) a hot restart can need for a
  minute or two (`practice` 037).
- Raising closed-loop P from the default 0.1 to 2 made AFR hunt, and at 5 trims swung limit to limit. Transport
  delay is long at idle and short at WOT, so one gain is a compromise; watch WOT behaviour closely (`practice`
  037).
- Neighbouring cells needing -10 % and +15 % produced an AFR spike near 18:1 on a quick 45 to 50 kPa move before the
  loop caught up. Closed loop cannot hide a rough base map from the driver (`practice` 037).
- Overboost protection has an absolute MAP cut and an over-target margin, and resets only after throttle drops by a
  set amount. The example file carried a 200 kPa over-target margin, which the practitioner called far too generous;
  check it in any inherited tune (`practice` 039).
- The coolant-indexed rev limit cannot raise the main limiter: the main limit still wins over higher values in that
  table (`practice` 039).
- Lean protection without a delay trips on shift cuts and sensor transport delay. The session arms it only at high
  load and uses about 0.5 to 1 s delay, shorter on very high output engines where one second lean is fatal
  (`practice` 039).
- On plug-in packages, oil pressure, fuel pressure and oil temperature must go to fixed predefined pins, and
  protection strategies are limited to those AEM provides; the practitioner compared this with other plug-in packages
  that also lock pins. Set each sensor's failsafe value so a fault triggers protection (0 psi oil pressure in the
  example) (`practice` 039).

### Drive-by-wire
- Sample pedal 100 % with the pedal pushed hard into its stop. A gentle press stores a low maximum, and a driver who
  stamps harder exceeds it and can set an error (`practice` 178).
- Tune the bias (open-loop duty) table with P, I and D at zero first, with breakpoints about 1 to 1.5 % either side of
  rest plus 0 and 100 %. The opening side needs more duty (35 to 40 % in the demo) because it fights the return
  spring; the closing side goes negative. The tracking-error shutdown has to be disabled for this and re-enabled after
  (`practice` 178).
- Throttle PID gains are specific to each throttle body and wrong gains can lose control of the throttle. Start from
  AEM's gains for that body. Hand tuning in the demo: P of 6 fluttered, 10 oscillated, 2 was clean, I about half of P,
  D about 0.05 (`practice` 178).
- The DBW idle range sets the throttle that 100 % of the idle position table represents. If a cold engine cannot
  reach idle target whatever base values are entered, the range is too small (raise 6 % to 8 to 10 %); 15 to 20 %
  makes the table too coarse (`practice` 178).

### Logging
- Lambda relayed over CAN to the dyno software updated far too slowly to use during a ramp run; use the ECU's own log
  for lambda against target (`practice` 8.23). The dyno's CAN-received ignition angle was still useful for
  plotting torque against timing at a held cell (`practice` 8.22).

### Older AEM products
- Series 1/2 on Honda time-based tables (and similar time-based systems where only dead time is entered): in the 3D
  view, a hump at idle and light load above the table's trend means dead time is set too low; a sunken region means
  too high. Flow error scales the whole table instead. Fix dead time until the surface flows smoothly
  (`practice` bad injector data).
- Series 2 offers a ground-speed traction limiter (rpm per gear against vehicle speed). It needs speed from an
  undriven wheel, filled from the rpm logged at each speed in the best run (`practice` traction control).

## Worked example

A VQ35 on the Infinity at 2000 rpm, 50 kPa, closed loop on below 80 kPa. Lambda reads 1.00 on target, trim reads
+4 %. The cell is lean by about 4 %: multiply VE by 1.04 and trim falls to about 0. At WOT, closed loop is off and
the log shows lambda 0.83 against target 0.88 at 5000 rpm with MAP 96 kPa. The correction factor is
0.83 / 0.88 = 0.943. The cursor sits between the 90 and 100 kPa rows, so both rows at that rpm are multiplied by
0.943; the corrected-VE channel suggests the same number. Had MAP been bouncing 90 to 97 kPa, the filter would be
raised first, since a jumping cursor would make any correction unrepeatable.

## Disputed / conflicts

- **Closed loop at WOT.** One practitioner habitually disables it there, from experience with analog widebands that
  failed silently, but accepts full-range closed loop with modern CAN widebands that report faults if limits are
  tight (about 5 %). With a single global limit on this ECU, tight limits conflict with hot-restart needs. Test: log
  trim at WOT and after hot restarts on the car before choosing.
- **VVT failsafe on target error.** One practitioner does not rely on it, arguing the mechanical build should make
  valve contact impossible; others treat every available protection as worth setting. Never disable it on an engine
  whose valve clearance at full cam travel is unknown.
- **Data sets for the same injector.** Injector-maker and ECU-maker dead times disagree by about 0.16 ms at 14 V.
  Neither is wrong for its own driver; the discriminating test is lambda at idle after swapping data sets with VE
  unchanged.

## Citations

- practice: Practitioner training and tuning practice, distilled and cross-checked.
