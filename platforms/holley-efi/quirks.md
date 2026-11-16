---
id: platforms/holley-efi/quirks
title: Holley EFI quirks
layer: L3
confidence: medium
sources: [practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/holley-efi/semantics]
supersedes: []
---

# Holley EFI quirks

How Holley's Sniper 2 (throttle-body injection, touchscreen and laptop), HyperSpark distributor and Terminator X /
Terminator X Max behaved in training material: a carburetted small-block V8 converted to Sniper 2, and a stock LS1 in
a C5 Corvette (automatic) on Terminator X Max. Lessons carry largely across Terminator X, HP and Dominator because the
software is similar. What settings mean is in `semantics.md`. Tags `practice` and `practice` mark the
training source.

## Claim

Holley systems are built around self-learning: a fast closed-loop trim feeds a slow, persistent learn table that
spreads into neighbouring and unvisited cells. Zero closed-loop trim therefore does not mean the base table is
right; only trim plus learn tells the base error, and the learn table needs human editing before transfer. Other
traps: editing an axis breakpoint does not re-interpolate the cells; default closed-loop authority is huge; the IAC
"parked" table is the start-up position; the throttle stop sets whether idle control has authority; and some
setups give no timing offset or only 360 degrees of it.

## Why (derivation)

- Short-term trim corrects the error now; learning then moves that correction into the learn table and the trim
  decays toward zero. At steady state the total correction is the sum, so either part alone underestimates it.
- The learn table spreads a correction around the active cell and fades it with distance. Cells the engine never
  reached therefore carry partial, extrapolated values, and different sessions can leave opposite signs in adjacent
  regions.
- A table that keeps cell values when its axis moves now delivers each number at a different rpm or load, which is a
  change of tune.
- An idle air valve can only reduce air down to what the throttle stop already passes. If the stop passes too much,
  the valve sits at zero and the controller has nothing left but spark.

## Assumptions

- Sniper 2 and Terminator X software of the period shown; Holley's base calibrations for common domestic V8s.
- A batch-fired TBI with a coil-negative speed input for the Sniper; a 24x crank LS1 for the Terminator X.

## Breaks when

- Later Holley software may add re-interpolation, per-region authority on the handheld or different learn
  spreading.
- Multipoint or sequential Holley setups need crank and cam position, so the TBI trigger remarks do not apply.
- Knock-control opinions are one practitioner's and may not hold on other software versions.

## Practical use

### Reading closed loop and learn together
- Read short-term closed-loop trim and the learn value for the same area together. A cell with 0 % trim and -10 %
  learn is 10 % rich in the base table, already absorbed (`practice` 8.92, 8.107, 8.108).
- Learning starts only when the engine is fully warm; closed loop acts sooner. At a Sniper first start AFR began near
  9:1 and closed loop pulled about 8 % but learn stayed inactive, so that trim is not yet a VE correction
  (`practice` 8.90).
- Closed loop and learning both drop out whenever acceleration enrichment is present. Brief inactive flags during
  quick throttle moves are expected (`practice` 8.94).
- A cell is finished when warm-up enrichment reads 100 % (inactive) and short-term trim has returned within about
  1 % while learn absorbed the correction (`practice` 8.94).
- In one Sniper session learn cells at 105 kPa held about -17 next to -33 at 101 kPa on an NA engine at 97 to
  98 kPa ambient, and cells just past the highest rpm visited were populated. Treat learn values in unvisited cells
  with suspicion (one practitioner's observation, `practice` 8.94).
- After one Terminator X dyno session the learn table was jagged: recent corrections spread back into areas already
  learned, a 2 to 3 % correction faded to about 0.3 % in unvisited cells, and whole regions stayed empty. At idle the
  real correction was about -7 to -8 % while nearby cells looked nearly perfect. Pressing transfer without review
  bakes these artefacts into the base table (`practice` 8.108).
- Edit the learn table before transfer: copy trusted rows or columns into unvisited areas, set a consistent value
  where the trend is known, interpolate, and investigate sign flips or isolated outliers (one cell at 10 % among
  cells near 2 %) instead of merging them. After road driving the course also scaled extrapolated low-load areas by
  0.5 and halved the whole table before transfer, then smoothed (`practice` 8.89, 8.108, 8.111).
- Healthy, well-learned Sniper: short-term trim near plus or minus 2 to 3 %, learn may hold 15 to 20 %
  (`practice` 8.83). Two self-learn ramp runs reached about what six or seven manual runs did (one practitioner's
  experience, `practice` 8.98).
- Log viewer default span for trim channels is plus or minus 999, which makes learn look flat. Rescale to about 10
  (`practice` 8.99).

### Authority limits
- Default closed-loop authority is very wide: plus or minus 100 % on the Sniper; 50 % for closed loop and 50 % for
  learn on the Terminator X, about 100 % combined. Useful while roughing in, risky afterwards, since a faulty sensor
  can then drive fuelling (`practice` 8.83, 8.100, 8.108).
- After tuning, the course used about 5 % at high load (79 kPa and above on the NA LS1), 10 % at cruise and 15 % at
  idle, where heat soak is largest, and either disabled learn or pulled its authority back similarly. On the Sniper
  handheld only one value can be set (no idle, cruise and WOT split as on the laptop), so 20 to 30 % was used as a
  compromise (`practice` 8.100, 8.108, 8.111).
- If high-load areas need more than about 5 % trim, the base table needs work rather than more authority
  (`practice` 8.83).
- For dyno hand-tuning, one practitioner turns long-term learning off and keeps short-term closed loop, then
  re-enables learning with about 5 to 10 % authority for a couple of weeks of driving and reads the learn table as a
  report card on the dyno tune (`practice` 8.89).

### Table editing traps
- Changing an axis breakpoint does not re-interpolate the column or row: the old values stay put at the new axis
  value. Finalise breakpoints (load a little past maximum MAP, rpm a little past the limiter) before tuning
  (`practice` 8.86, 8.104).
- Default axes can leave a boosted engine with most rows in vacuum and all boost in a few rows; rescale with the fill
  function before tuning (`practice` 8.104).
- The Terminator X ships about a 31 by 31 VE table, far finer than needed but probably sized for learning. Sniper
  base tables are also very dense near idle (`practice` 8.86, 8.104).
- Switching AFR or spark from simple 3-point mode to a full table on the laptop locks the handheld out of those
  parameters (`practice` 8.87).
- Injector capacity warnings in 210 kPa rows on an NA engine are irrelevant (`practice` 8.86).
- Compensation tables can hold hidden corrections. Check coolant enrichment is 100 % at operating temperature (about
  180 F), no AFR offsets act in the operating area, and timing against coolant and IAT; their axes default to a
  useless 999 F (`practice` 8.104).
- Global timing limits defaulted to -45 to +60 degrees; the course clamped them to about -10 to +40/45 for a pump-gas
  LS so no table error can go far (`practice` 8.102).
- Custom dead-time voltage breakpoints straddle 14 V (13.6 and 14.4) and run to 20 V; interpolate supplier data onto
  those points rather than copying cell for cell (`practice` 8.102).
- Many configuration parameters are locked while online, and output test runs only offline (`practice` 8.102).

### Setup inputs that skew the base map
- Sniper cam choice (stock to race) shapes the generated VE. A race cam entered as stock will likely idle very rich
  and may be lean under load (`practice` 8.83).
- The fuel pressure set at the regulator must match the value entered; the ECU uses the entered value (`practice`
  8.83).
- Closed loop enables above a coolant threshold (160 F default). For an untuned first start the course lowered it to
  about 100 F so trims help early, then restored it (`practice` 8.87, 8.89).
- At a Terminator X first start, AFR read on target with closed-loop trim already near -20 % and coolant enrichment
  adding 13 to 15 %. The base was pulled in 3 to 4 % steps; removing 20 % at once would swing lean as the loop
  reacted (`practice` 8.106).

### Idle (Sniper IAC and Terminator DBW)
- The IAC parked table is the start-up position, not the return-to-idle base position (that is the hold setting).
  Tune it so the engine fires and flares only 100 to 200 rpm above target (`practice` 400).
- Return to idle uses a hold position (default 30 % IAC), ramp start rpm, decay time and closed-loop re-entry above
  target. Too fast a decay stalls; too slow hangs. Start-up air holds 4 s then decays over 4 s (`practice` 400).
- Hot idle above target with IAC at 0 % means the throttle stop passes too much air; idle spark then pulls a lot of
  timing to hold rpm. Adjust only the primary stop screw. Aim for about 5 to 12 or 5 to 15 % IAC at hot idle (10 % as
  the middle). TPS must read 0 at closed throttle: above about 2 % the Sniper will not chase idle. After moving the
  stop, power off for about 5 s so closed throttle is relearned (`practice` 8.91, `practice` 400).
- Idle spark uses P and D only; with zero D it overshoots and hunts. Disable it while setting idle air so it does not
  hide a baked-in error (`practice` 400).
- Terminator X flare straight after start comes from the DBW startup park position and hold time; the course cut hold
  from about 4 s to 2 s with a 2 s decay, then stepped the target (600, 750) to check control (`practice` 8.107).

### Ignition, trigger and distributor
- A Sniper TBI fed from coil negative needs only engine speed (spark frequency and cylinder count), because it
  neither sequences injectors nor fires coils per cylinder (`practice` 8.85).
- With a mechanical distributor, ignition tuning means rotating it to move the whole curve. HyperSpark gives full
  cell control. Its inductive delay (100 microseconds start value, 57.5 degree reference angle per the manual) is set
  so locked timing stays put from idle to 4000 to 5000 rpm, where uncorrected drift is typically 1 to 2 degrees
  (`practice` 8.82, 8.88).
- Simple 3-point spark has one cruise value; MBT moves with rpm and load, so on a knock-limited engine a value
  optimised at 3000 rpm can be over-advanced at 2000 (`practice` 8.96). Terminator X simple-mode defaults were 12
  idle, 36 cruise, 26 WOT degrees; the course converted to a full table, raised idle to about 16 and pulled 4 degrees
  from WOT before first start (`practice` 8.104).
- On the Terminator X the ignition type also defines trigger inputs. Predefined types such as LS 24x fix dwell and give
  no timing offset, inductive delay or dwell setting; tolerance can still shift timing slightly, and there is no way
  to correct it. Verify with a light anyway and check the firing order table (`practice` 8.102, 8.103).
- With a single VR arming value, start near 0.3 V and raise it as far as triggering allows (`practice` 8.103).
- A Terminator whose timing looks right on the light but will not run may be synchronised 360 degrees out. The
  software allowed only about 360 degrees of offset, so the fix shown was to swap the single-pulse cam edge from
  rising to falling, or back (one practitioner's account, `practice` 431).
- Built-in knock control was judged too simple to be worthwhile by one practitioner on both Terminator platforms; use
  audio knock detection when tuning (`practice` 8.102, `practice` 431).

### Load model and installation
- For big cams with poor idle vacuum, Terminator X offers a combined mode: alpha-N at idle, MAP-based VE above set TPS
  and rpm thresholds (`practice` 8.102).
- On a modern car the course ran the Terminator X Max alongside the retained factory ECU so other modules stayed
  happy (`practice` 8.101).
- Sniper 2 injector size limits it to roughly 650 hp NA; a 150 to 170 hp V8 peaked at about 24 % duty. TBI has no
  per-cylinder trim and no injection timing, and suits low to moderate power street conversions (`practice` 8.82,
  8.97).

## Worked example

Terminator X, stock LS1 at idle, learn active. Log: closed-loop trim 0 %, measured AFR on target, learn monitor
-10 %. The base VE at idle is about 10 % rich (factor 0.90), not correct. Near the top of a ramp run closed loop is
pulling 8 % and learn 2 % at 6000 rpm, a total near 10 %: multiply that column by about 0.95 (half the error, as the
course does for large errors), extend the change to higher columns since VE keeps falling, and re-run. Meanwhile a
learn cell at 105 kPa on an NA engine at 98 kPa ambient is ignored: the engine never got there.

## Disputed / conflicts

- **Learn during dyno tuning.** One practitioner keeps learning on during ramp runs because it helps fill high rpm; the
  same course elsewhere turns long-term learning off while hand-tuning so learn later grades the dyno tune. Both
  narrow authority afterwards.
- **Disable learn once tuned.** One view disables learn when done; Holley's design and the handheld workflow expect
  periodic learn-then-transfer cycles (`semantics.md`). Test: watch learn growth over a few hundred road miles with
  tight authority.
- **Small negative trims.** The course leaves slightly negative residual trims alone on the basis that a little rich
  is preferable to a little lean; a mechanical ratio correction would remove them. Choice, not a measurable
  conflict.
- **Built-in knock control.** One practitioner finds it ineffective; no source in this set validated it either way.

## Citations

- practice: Practitioner training and tuning practice, distilled and cross-checked.
