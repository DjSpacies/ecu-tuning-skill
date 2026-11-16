---
id: platforms/megasquirt/quirks
title: Megasquirt quirks
layer: L3
confidence: medium
sources: [practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/megasquirt/semantics]
supersedes: []
---

# Megasquirt quirks

How Megasquirt (MS2, MS3 Pro, MicroSquirt) and TunerStudio behaved in training material, mostly on a 1989 Mazda MX-5
with the B6 1.6 L on an MS3 Pro, plus MS2/Extra project setup. What settings mean is in `semantics.md`. Tags
`practice`, `practice` and `practice` mark the training source.

## Claim

With Megasquirt the commonest traps are in the software workflow and in a few strategy defaults: changes live only
in RAM until burned and Escape closes a table instead of undoing; typing a new axis value does not re-interpolate
the cells (the axis editor does); breakpoint counts are fixed; barometric pressure is sampled once at key-on; fixed
timing does not apply while cranking; EGO correction reads around 100 % and on-target lambda can hide a few percent
of base error; default closed-loop PID gains performed poorly; and the fuel table is true VE only with multiply-MAP
and AFR-target incorporation enabled and stoich set.

## Why (derivation)

- TunerStudio sends edits to controller RAM. Flash is written only on burn, and power-down reloads flash.
- Required fuel is the pulse width at 100 % VE and 100 kPa from displacement, cylinders, injector flow and AFR.
  Multiply-MAP scales it by manifold pressure, and incorporating the AFR target scales it by stoich over target, so
  the remaining table value is cylinder filling.
- A baro reading taken at key-on is a constant for the drive. Driving to a different altitude changes real ambient
  pressure and so the air estimate's reference.
- EGO correction is a multiplier around 100 %: above 100 adds fuel because the cell is lean.

## Assumptions

- MS3 Pro and MS2/Extra 3.4.x firmware with TunerStudio of the period shown; features depend on box and firmware.
- A naturally aspirated, batch-fired B6 on its factory harness for most examples.

## Breaks when

- Different MS hardware or firmware builds expose different settings; let TunerStudio detect the firmware.
- A dedicated baro sensor removes the key-on sampling limit.
- Default gains and filters change between firmware releases.

## Practical use

### Software workflow
- Edits are live but volatile until Burn; watch the needs-burn indicator. Escape closes the table rather than undoing
  an edit as on other platforms (`practice` 216, 231; `practice` MegaSquirt basics part 3).
- On first connection, save the controller's existing tune as an untouched original .msq, then save timestamped
  revisions. Loading or sending a tune is not persistent until burned (`practice` part 3).
- Creating a project: power the ECU, use firmware detect so it finds the port and firmware (MS2/Extra 3.4.2 in the
  example), confirm the comms test, and record engine details in the project description. On a fresh install a
  custom project name made the wizard fail in one account; keep the default and rename later (anecdote,
  `practice` part 2).
- Typing a new axis value does not re-interpolate the cells, so a tuned table becomes wrong. Use the axis editor
  option that applies new axis values and re-interpolates the cell values (`practice` 216, 231).
- Tables have a fixed breakpoint count that cannot be deleted. On an NA engine whose table spans into boost, choose
  between more vacuum resolution and unused boost rows (`practice` 8.159).
- Keyboard: period and comma step by 0.1, with Ctrl by 0.5; Shift-asterisk multiplies a selection (1.05 adds 5 %);
  equals sets a value; slash interpolates (`practice` 216).
- TunerStudio highlights the cell when the operating point is close to its centre. Off-centre (2960 to 2980 rpm when
  aiming at 3000) an edit is spread into neighbours; use the dyno set point to sit centrally (`practice` 216).
- Logs: start the log before cranking a no-start and crank 5 to 20 s. Logs go to the project's DataLogs folder with
  timestamped names; rename for test sequences (`practice` part 4).

### Fuel equation and its options
- Enable multiply-MAP almost always and incorporate AFR target with correct stoich (14.7 for pump gasoline). Then
  mixture changes are made in the target table only, provided the mechanical setup is unchanged. Targets must be
  set before tuning (`practice` 8.157, `practice` 216, 231).
- Required fuel for the stock B6 was 11.7 ms (`practice` 8.157).
- The lambda target table holds its last column beyond the last breakpoint (6000 rpm axis, 7500 rpm engine), so
  targets still exist above it (`practice` 8.159).
- Base VE: the generator (NA, idle about 800 rpm at 35 kPa, redline, guessed peak torque and power rpm, displacement)
  gives a shaped start useful on the road; a flat 50 to 60 % fill is the alternative. Tuned idle cells on the B6 ended
  at about 47 to 49 %. Generated tables drifted further off as load rose (about 10 then a further 7 % rich from
  60 kPa up), so correct the remaining higher-load cells in the column ahead of time (`practice` 8.159, 8.163,
  `practice` 231).
- Short pulse-width non-linearity cannot be measured by the tuner. Without the injector maker's small-pulse adder data
  the error is absorbed into idle and light-cruise VE (`practice` 231).

### Closed loop (EGO) and autotune
- Lambda on target with AFR error zero but EGO correction at about 104 % (or 96 %) means the cell is about 4 % lean
  (or rich). Multiply the active cells by the correction and confirm it returns to about 100 % (`practice` 231).
- Default PID gains for EGO control performed poorly on the B6. What worked: low P, relatively high I, very little D,
  since the system was very sensitive to D. Also use valid-lambda windows (rejects overrun readings), a start delay
  (30 s) so the sensor is hot, and optionally disable above a throttle threshold (60 to 70 % TPS) (`practice`
  231).
- Oscillation about target from transport delay is handled with an rpm-based EGO delay table, about 1000 ms at idle
  tapering to about 50 ms by 5000 rpm in the session (`practice` 231).
- VE Analyze Live corrects the current cell and also tunes ahead into neighbouring higher cells. Heat soak, warm-up
  enrichment and acceleration enrichment corrupt it, so filter on rpm, load and coolant and add a custom filter
  excluding AE-active samples; drive smoothly and start and stop it selectively (`practice` 216, 231).

### Sensors, triggers and ignition
- Baro from the initial MAP reading is sampled once at key-on. Fit a dedicated baro sensor if the car climbs or
  descends a lot in one drive (`practice` 8.157).
- Spark output polarity: most systems need going high, some (certain Honda) going low; wrong polarity can burn coils.
  Leave coils unplugged until ignition output settings are confirmed (`practice` 8.157).
- Skip pulses (default 3) ignore the first few edges at crank start. Predictive ignition helps low-tooth patterns when
  rpm changes fast (`practice` 8.158).
- Sync check with coils and injectors unplugged: stable cranking rpm (about 260 on the B6), sync flag set, lost-sync
  counter not incrementing once rpm is steady. A few counts at crank start are acceptable (`practice` 8.158).
- The 1989 B6 cam-mounted optical sensor uses the 4G63 decoder; the similarly named later Miata decoder is wrong for
  it (`practice` 8.158).
- While cranking, the ECU uses the cranking advance (13 degrees in the base), not fixed timing. Set both to the same
  visible value (10 degrees on the B6) when calibrating, then return to the table (`practice` 8.160).
- On the factory MX-5 harness injectors are paired, so it runs batch fire with two drivers (two squirts, alternating)
  unless rewired (`practice` 8.157, `practice` 216).
- The stock B6 has only an idle switch. Fit and calibrate a proper TPS; a wrong closed reading upsets idle control
  (`practice` 8.157).
- Knock control was judged against what useful detection needs: tunable centre frequency, an angle window after TDC,
  per-cylinder gain and per-cylinder retard. A mild NA engine is a poor test bed (one practitioner's view,
  `practice` 216).

### Idle (MS3 Pro)
- The PWM idle valve shares its frequency with boost control. The boost solenoid is usually more sensitive (3-port
  types around 20 to 30 Hz); the demo idle valve ran at 99 Hz with no boost control (`practice` 266).
- Cranking idle duty against coolant: 40 % started hot and settled about 800 rpm, 60 % flared to 1600 to 1700. Tune
  for a 100 to 200 rpm flare at a cold and a hot point and interpolate; crank-to-run taper blends to running duty
  (`practice` 266).
- The closed-loop initial value table is the feed-forward duty on entering idle. Rpm hanging high means it is too
  high; dipping or stalling means too low. Zero the PID gains to tune it as open loop, then restore (`practice`
  266).

### CAN
- Broadcast fast channels (rpm, MAP, TPS) at higher rates than slow ones; sending ignition advance to the dyno lets
  it plot torque against timing (20 Hz in the demo, `practice` 216).

## Worked example

B6 at 2000 rpm, 60 kPa, EGO on. TunerStudio shows AFR error 0, lambda 1.00 on target, EGO correction 104 %. The cell
is 4 % lean: select the cells being interpolated, Shift-asterisk by 1.04, and EGO correction returns to about 100 %
with lambda unchanged. Burn. The rpm axis is then moved from 2000 to 2250 by typing the value: the old numbers now
apply at 2250 and the 2000 rpm area is wrong. Undo by reloading the burned tune, and use the axis editor's
re-interpolate option instead.

## Disputed / conflicts

- **Flat versus generated base VE.** One session prefers a flat 50 to 60 % fill because it avoids guessing a shape;
  the course uses the generator, especially for road tuning without a dyno. Both refine cell by cell. Test: time to a
  stable first start and number of edits to reach target in the first block.
- **Autotune value.** One practitioner calls it garbage in, garbage out and matchable by an experienced tuner by hand;
  the same sessions find it most useful on the road where the driver must concentrate on driving. Both demand
  filters for AE, warm-up and idle.
- **Overrun pops.** One session attributes deceleration pops mostly to overrun fuelling and offers either overrun fuel
  cut or accurate low-load VE; other causes (exhaust leaks, ignition) are not discussed there.

## Citations

- practice: Practitioner training and tuning practice, distilled and cross-checked.
