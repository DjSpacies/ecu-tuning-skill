---
id: platforms/fueltech/quirks
title: FuelTech quirks
layer: L3
confidence: medium
sources: [practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/fueltech/semantics]
supersedes: []
---

# FuelTech quirks

How the FT600 (and, where the sessions say so, the FT450 and FT550) behaved in training material, on a GM LS1 in a
C5 Corvette with a returnless fuel system and an automatic gearbox. What settings mean is in `semantics.md`. Tags
`practice` and `practice` mark which training source showed the behaviour.

## Claim

The FT600 is an injection-time ECU that can display its fuel table as if it were VE. Most of its traps follow from
that: the percent-VE view is not engine VE; the lambda target drives only closed loop, so changing it does not change
the base fuelling; the wizard base map is shaped wrongly at light load and runs very rich; dead time has no
differential-pressure axis; DBW calibration is lost unless written and read back in the right order; and closed-loop
smoothing is a single value, so idle hunting and slow response elsewhere trade against each other.

## Why (derivation)

- In an injection-time model the table holds opening time (ms) per rpm and load. The ECU does not compute air mass
  from it, so there is nothing for a lambda target to scale. A VE "view" is a back-calculation from time, injector
  flow and assumed conditions; it inherits every error in those assumptions.
- Fuel needed per cycle falls as manifold pressure falls. A table that is flat below 40 kPa therefore over-fuels light
  load, and the error grows the lower the load.
- With fixed rail pressure on a returnless system, pressure across the injector rises as manifold pressure falls, so
  true dead time varies with load. A table indexed by battery voltage alone cannot represent that.
- Transport delay from injector to sensor is long at idle and short at high rpm. A single loop smoothing value
  cannot be right at both.

## Assumptions

- FT600 software and firmware of the era shown; the comparison with FT450/550 is the practitioner's statement.
- FT700, which has a true VE table (`semantics.md`), is not covered here.

## Breaks when

- FT700 or later firmware with a VE model and a pressure-indexed dead-time table.
- Base maps other than the wizard may not show the flat light-load shape.
- Automatic-gearbox dyno limits apply to the demonstration car, not to the ECU.

## Practical use

### What the fuel numbers mean
- The main table can be shown as percent VE, duty cycle, fuel flow (lb/h) or milliseconds. Tune in milliseconds;
  use the others as checks. The percent view showed about 79 % peak on a stock LS1, which looks low for true VE and is
  only an estimate. The duty-cycle view is a quick check of injector headroom (about 70 % at the top here)
  (`practice` 8.49, `practice` 427).
- Changing the lambda target alone only makes closed-loop trim work harder; the base table does not know about the
  target. To test whether the engine wants a different mixture, change both the target and the main table
  (`practice` 8.51, `practice` 427).
- Total injector flow (all primaries, about 210 lb/h on the stock LS1) scales the pulse-width table and the fuel
  consumption figure. When the separate dead-time table is used, set the single dead-time value to zero or dead time
  is applied twice (`practice` 8.49, `practice` 427).
- Dead time can be a single value (assumed at 14 V) or a battery-voltage table, but has no differential-pressure axis.
  On the returnless C5 (about 4 bar rail) the session chose values that match idle and light-load differential
  pressure, where dead time matters most, and accepted the error elsewhere (`practice` 427).
- IAT compensation in the base map did not make physical sense. The course set zero at 20 C, adding about 2 to 2.5 %
  per 10 C colder and removing the same per 10 C hotter out to about 60 C. This applies because the model does not
  compensate density itself (`practice` 8.51).
- An overall ignition trim and a TPS-based auxiliary ignition compensation exist; check both are doing nothing
  before tuning, or delivered timing will not match the table (`practice` 8.51).

### The wizard base map
- Because the needed pulse width depends heavily on injector size, a flat starting value is hard to guess, so the
  course used the wizard even though the practitioner would not usually. Evaluate it by eye before running
  (`practice` 8.49, `practice` 427).
- Signs seen on the stock LS1 wizard map: idle pulse width 6.3 ms against about 2.6 ms needed; the same value from
  40 kPa down to 0 kPa; WOT near 19 ms against 13 to 15 ms tuned; 25 to 29 degrees at 400 rpm and an odd timing dip
  at light load around 4000 to 5000 rpm; rpm breakpoints every 200 rpm up to 3000. From the shape alone the map
  predicts a very rich engine. It starts, but needs shaping (`practice` 8.51, `practice` 427).
- Simplify breakpoints to about 500 rpm with finer spacing at idle and off-idle, then add where the data asks: a
  35 kPa row where idle sat at 34 kPa between 30 and 40, and a 4250 rpm column where 4000 and 4500 were right but the
  ramp run was off between (`practice` 8.55, 8.57).
- At first start, move the whole table coarsely, assuming the idle error applies everywhere, aiming roughly for 0.90
  to 0.95 lambda (`practice` 8.53).

### Closed loop and the correction overlay
- Closed-loop O2 correction falls a long way as the engine warms (13 % at first start to about 2 % at 80 C in the
  course). Do not chase cold trims as base-table error (`practice` 8.54).
- With closed loop holding target, the trim value is the base error: holding 0.95 lambda by adding about 5 % meant
  multiplying the interpolated cells by 1.05, after which trim read about 1 % (`practice` 427).
- Closed loop has one low-load smoothing value and no delay table by rpm. The default (about 6) hunted rich and lean
  at idle; 20 to 25 stopped it but made steady-state work at 2500 to 3000 rpm slow. Raise it until idle stops
  oscillating and accept slower response elsewhere (`practice` 427).
- The O2 correction overlay bins average trims into map cells and can apply them. It changes only visited cells, and
  shows values from cells barely crossed. With no sample count shown, uncheck all and apply only well-covered areas,
  then extend by hand into neighbouring and unvisited extrapolated cells, slightly underestimating (`practice`
  8.57, 8.58, `practice` 427).
- For road data before transient fuel is tuned, the course lengthened the closed-loop freeze after a transient event
  (0.15 s to 0.4 s) so trims do not learn transient error, and restored it after (`practice` 8.58).
- Closed-loop authority ships wide (plus or minus 30 % everywhere on the demo). The course narrowed it to about 20 %
  up to 40 kPa, 10 % around 60 kPa and 5 % at WOT once the base map was right (`practice` 8.58).

### Sensors, triggers and ignition
- Ignition output edge: falling edge for almost all coils, rising for some (MSD, some Honda distributors); the wrong
  edge can destroy coils quickly, so ask FuelTech if unsure (`practice` 8.49).
- Powered only from USB, the ECU is safe to configure (coils unpowered), but I/O readings are meaningless until the
  vehicle is powered (one practitioner's note, `practice` 8.49).
- Sensor averaging: about 60 points for temperature sensors, about 7 for fast pressure sensors, otherwise as little as
  possible (`practice` 8.49).
- Custom NTC sensors are entered as voltage against temperature, so convert the sensor's resistance table with the
  ECU's internal pull-up (thought to be about 1 kohm in the session) and enable the pull-up (`practice` 427).
- The LS1 crank sensor is magnetic but has internal conditioning, so it is set as Hall with pull-up, falling edge;
  the LS1 is 24x, many later LS engines 58x (`practice` 8.50).
- Single-tooth cam sync position is refined from the diagnostic display of measured cam angle while running (about
  3 degrees here), not at cranking (`practice` 8.50).
- Base timing uses fixed-timing mode, which ignores tables and compensations. Check at a steady 750 to 800 rpm
  idle, since timing wanders at about 180 rpm cranking (`practice` 8.52).

### Idle and drive-by-wire
- Select the exact throttle body model so suitable PID values load; unlisted bodies can be sent to FuelTech for
  characterisation (`practice` 8.49).
- After pedal and throttle calibration, write to the ECU and read back in the required order, or the calibration
  appears lost after every power cycle (`practice` 8.49, `practice` 427).
- FuelTech recommends the fixed idle actuator position (table) mode over automatic PID; idle ignition control still
  chases target in fixed mode (`practice` 8.54). In a separate session automatic mode hunted at first and a lower
  reaction setting (2) gave stable idle; there is a plus or minus 25 rpm deadband and few other controller settings
  (`practice` 427).
- Idle ignition overrides the base ignition table at idle, so the base value there is used only on the way out of
  idle; the course set it 15 to 18 degrees and blended to the tuned 1500 rpm column (`practice` 8.56).
- To check idle authority, widen the idle ignition limits (0 to 22 degrees), step the target and watch rpm follow:
  ignition alone was slow; 0.5 % throttle steps visibly moved rpm on the DBW LS1 (`practice` 8.54).

### Dyno limits seen with this car
- Behind an older automatic (4L60), the converter flared as load rose at low rpm, so full-load cells around 1500 rpm
  could not be held and were extrapolated (`practice` 8.55).

## Worked example

Course data, LS1, millisecond view. At 1500 rpm, 35 kPa the trim reads about +19 to 20 % because the column still
held idle-derived values. The error is global to the column, so multiply the whole column by 1.15 (deliberately
under the error), then refine the active cell and the unreachable cells below by a further few percent, then fine
steps until trim sits within 1 to 2 %. Move to 2000 rpm by copying the tuned column and adding a guessed 5 %; the
trim says that was 4 % too much, so the next column gets a 3 % guess. Changing the lambda target from 0.95 to 0.90
at this point would not enrich the base table; it would only push trim up by about 5 %.

## Disputed / conflicts

- **Injection-time versus VE model.** One practitioner says neither is inherently right, but a VE model suits flex
  fuel better because VE barely changes with ethanol content (opinion). FuelTech's own FT700 moved to a true VE table
  (`semantics.md`). No discriminating test on the FT600 itself.
- **Idle control mode.** FuelTech recommends fixed position; one session found closed-loop position control
  workable once the reaction setting was lowered and preferred it. Test: log idle rpm error over warm-up and
  accessory loads in each mode.
- **Overlay auto-apply.** The course prefers manual application for ramp runs; the same practitioner sees value in
  auto-apply for long, varied road logs where manual analysis is impractical.

## Citations

- practice: Practitioner training and tuning practice, distilled and cross-checked.
