---
id: platforms/link-g4plus/quirks
title: Link G4+ quirks
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/link-g4plus/semantics]
supersedes: []
---

# Link G4+ quirks

Tags: `vendor-doc` (PCLink G4+ 5.6.8 help), `re-derived` (reverse-engineering notes), `sample-observed` (vendor
sample tunes and logs), and the training source ids `practice`, `practice`, `practice` for behaviour seen
by tuners on real cars (G4+ and ViPEC of that era). What settings mean is in `semantics.md`; this file is about how the
product actually behaves and the traps it sets.

## Claim

Most G4+ surprises come from a small set of behaviours: limits that start cutting before the number entered; the
lowest of several active limits silently winning; newly enabled or re-dimensioned tables holding junk or losing
values; tuning aids that compare measured lambda with target while ignoring other active corrections; edits that are
lost unless stored; and channels whose meaning depends on configuration (gauge versus absolute pressure, knock gain,
closed-loop trim). An agent reading a G4+ tune or log should test for these before diagnosing the engine.

## Why (derivation)

- Limits are proportional controllers: cut rises across a control range that ends at the table value, so cutting
  begins one range below it (`semantics.md`, Limits). With several limits active the ECU takes the minimum, so a
  forgotten table whose safe value equals today's rev limit caps tomorrow's.
- Tables are allocated from memory slots. Enabling a new table, or switching a 2D table to 3D, does not initialise the
  contents to anything meaningful.
- Mixture Map and Quick Tune work from measured minus target lambda. Any other fuel change that was active at the time
  (closed-loop trim, warm-up, accel enrichment) is not removed from that comparison, so the suggested correction is
  biased by it.
- Closed-loop controllers in this generation act on error alone with stage switching; a controller that looks perfect
  under the steady, repeatable load of a dyno can still misbehave when load and gear change on the road.

## Assumptions

- G4+ firmware 5.6.x and the PCLink of that era; training sessions were recorded on various G4+ and ViPEC firmware,
  and some behaviour (for example the boost derivative issue) may have been changed in later firmware.
- Default settings as shipped; a vendor base map may differ.

## Breaks when

- Firmware differences beyond 5.6.5 and 5.6.6, the versions in the samples, are unknown.
- G4X and G5 use different software and ids; none of these quirks carry over without checking.
- Training observations come from a handful of cars; a behaviour reported once (one practitioner's experience) may be
  car-specific.

## Practical use

### Adapter and file facts
- `sample-observed`: load axes in the samples are often gauge (MGP), running to -85 kPa, while MAP is absolute. Check
  which one a table uses before reading a value across. In the training sessions the MAP gauge axis is shown inverted
  by default (`practice` session 294).
- `sample-observed`: most samples use Traditional mode (34 of 44 tunes with the field), 9 Modelled and 1 Multi Fuel.
  Do not treat a fuel table number as VE without checking the mode.
- `sample-observed`: wideband inputs are named by the tuner (`An V2 - WideBand`) and one sample logged a blank unit with
  AFR-scale values. The adapter flags its conversion.
- `sample-observed`: the first log sample can be all zeros.
- `sample-observed`: one vendor tune contains character references that XML 1.0 rejects, in a label field. The parser
  replaces them with spaces, and only there.
- `re-derived`: the same name can map to several DataIds across generations (`Fuel Table1 G4`, `FuelTable1`,
  `Fuel Table2`). `tables.yaml` lists only the ids seen in G4+ tunes.
- `re-derived`: tables outside fuel, ignition and lambda target live in generic allocation slots (`G4 Table 1` to
  `12`, about 40 ids). What a slot holds depends on the tune's allocation, so boost tables have no fixed id and are not
  parsed. Unused second tables have flat filler axes and are skipped. Tuners note a fixed budget of 3D tables (30 on
  one unit) and save slots with 2D tables or gear trims where full 3D control is not needed (`practice` open-loop
  boost).
- `sample-observed`: the 45 tunes carry RPM and MAP limits as 18-point arrays, lower when cold (rpm_limit sometimes
  4000 to 4500 for the first few points).
- `vendor-doc`: fuel table load and equation load are separate settings. The table's axis does not tell you how the
  equation estimates air charge.

### Limits that act early or not at all
- The rev limit starts cutting one control range (default 200 rpm) below the table value; MAP limits have the same
  structure (10 kPa in one course lesson, 20 kPa in another session). Symptom: the engine "hits the limiter" at 6500
  with 6700 entered, or a boost cut appears below the MAP limit. Enter the start figure plus the range. One course
  lesson was caught by this and raised the limit to finish top-end tuning.
- The lowest active limit wins. A GP limit (oil pressure, lambda, flat shift) whose safe area holds the same value as
  the main limit makes a later rev-limit increase appear to do nothing. Fill safe areas with an unreachable value
  (10000 rpm in the sources).
- In advanced mode, an End Cut below 100 % with no hard cut may not limit at all: with End Cut at 60 % rpm climbed past
  the limit, and even at about 42 % throttle a VQ35 needed 70 to 80 % cut to hold rpm. With End Cut 85 %, rpm crept
  more than 50 rpm over and tripped the hard cut. Either set End Cut to 100 % or always enable a hard cut a little above
  the limit (`practice` sessions 084, 171).
- Start Cut at low throttle left at 0 is ignored, and only the 100 % throttle value is used.
- A cut that appears at the top of a pull when the driver lifts may be the lean protection GP limit, not the rev limit
  (`practice` RB25 part 4). Check the limiter status channel and which limit was active.
- A conservative boost cut set before first start is easy to forget: a sudden "misfire" as boost is raised during
  tuning is often that cut (`practice` 8.115). Coolant-indexed limits make a cold car feel like it misfires; tell
  the owner.
- Default sensor fault limits of 0 V and 5 V are nearly useless; set them just inside the sensor's real span (for
  example 0.2 and 4.8 V on a 0.5 to 4.5 V sensor) and choose an error value that triggers the protection, since a
  faulted sensor's real value is unknown (`practice` session 036).

### Tables that arrive with junk
- Newly enabled tables (second VE, second target, flex ignition, boost tables) contain whatever was in memory; one demo
  found 0.755 lambda below 220 kPa in a fresh second target table. Inspect every newly enabled table and copy the
  first table across before tuning.
- Switching cranking or post-start enrichment from 2D to 3D wipes the values. Copy them out first and paste into the
  0 % blend row.
- Export and import carry axis breakpoints; copy and paste carries cell values only, so axes must already match.
- Base files can hold dangerous values: a wastegate duty table at 100 % requests maximum boost, and warm-up enrichment
  cells near operating temperature (with throttle on the second axis) can add fuel at light throttle on a warm engine.
  Zero warm-up from about 60 C up before tuning the main table (`practice` 8.148, 8.152).
- Boost trim tables (IAT, ECT, gear) can hold odd values and interpolate between breakpoints: a 100 % cut at 110 C
  already removes about half the duty at 105 C (`practice` session 131). Keep trims zero across the normal range.
- In closed-loop boost mode the base duty table defaults to throttle by rpm axes; re-axis it to boost target by rpm.
- The charge temperature approximation table has fixed axes on G4+ (rpm by MGP), so an NA engine still has boost rows;
  copy the 0 kPa row into them.
- A factory-reset unit has injection and ignition disabled and generic settings (eight cylinders); load the closest
  vendor base map instead of starting from reset (`practice` RB25 part 1).

### Fuel model traps
- Turning the lambda target function on or off after tuning shifts the whole tune, because it adds or removes a
  background multiplier.
- Changing Master Fuel shifts AFR everywhere unless the table is rescaled by the inverse.
- The traditional fuel cell caps at 150 in one practitioner's RB25 tune and several sources treat 100 as a practical cap
  on other units; if cells hit the cap and still need fuel, raise Master Fuel and rescale.
- Changing the charge cooling coefficient or the charge temperature table after the VE table is tuned invalidates the
  VE table.
- Injector flow and rated pressure fields are hidden in Traditional mode.
- psi breakpoints in the dead time table snap to the nearest kPa value, because the ECU stores kPa; harmless.
- Without a fuel pressure sensor, differential pressure assumes rail pressure equals the rated pressure entered.
- A fuel table "rich spot" between two breakpoints cannot be tuned out by editing the neighbours; that only mistunes
  them. Insert a breakpoint (accept the interpolate prompt so nothing changes), then trim the new row.
- At WOT an NA engine at altitude or with a restrictive intake sits below 0 kPa gauge (about 96 falling to 92 kPa
  absolute in one demo), so the ECU interpolates between the 0 and -10 kPa rows. Corrections must go to every row the
  cursor straddles (`practice` session 041).

### Tuning aids and closed loop
- `vendor-doc`: closed-loop lambda is a minor trim. A large persistent trim means a base-map problem.
- The G4+ has one symmetric closed-loop trim limit, not split by load or by rich and lean direction.
- Mixture Map compares measured with target only and ignores the closed-loop trim active at the time. Either log with
  closed loop off, or combine lambda error with the logged trim (for example in an external histogram). Set a minimum
  sample count (default 10) and centre tolerance: one cell with 19 samples suggested a 26 % change from a throttle-lift
  transient (`practice` session 041; `practice` part 34).
- Mixture Map writes corrections only where data fell, leaving scattered cells; blend by hand so the table stays
  smooth.
- Quick Trim with fuel and target tables on different load axes needs the target load entered by hand.
- Quick Tune in automatic mode can mark a cell done before lambda settles, so it later sits outside the band; road
  transients make this worse than on a dyno. One practitioner prefers manual triggering and resets drifting cells.
- On a V engine, if one bank's sensor jumps around (exhaust pulsation), use the stable bank alone for Quick Tune.
- Closed-loop lambda is suspended during accel enrichment, so trim does not fight a deliberate enrichment.
- Closed-loop trim that goes to zero at high rpm is usually a lockout (rpm, MAP, TPS, coolant, or rate-of-change).
- With nitrous active and the target unchanged, closed loop removes the fuel the overlay added.

### Knock readings
- Knock gain at 2 doubles the raw signal; on an Evo 8 with a flat-response sensor it gave readings near 1000 that
  meant nothing. Set gain 1 and recheck (`practice` Evo 8 part 4).
- A threshold of 1000 (the maximum) disables detection while keeping logging; use it to record the noise floor.
- One practitioner found G4+ knock levels inconsistent from pull to pull on two of three live-training cars, and saw
  retard on one cylinder only after a timing increase (one practitioner's experience). Treat onboard knock as a watch
  item until it proves repeatable on that car; isolate a suspect cylinder with its own trim. Another practitioner trusts
  a validated setup to about 99 % and uses per-cylinder knock to trim individual cylinders.
- A single marginal count on ethanol at modest timing points to a threshold set too low rather than real knock; on
  gasoline the same reading deserves more concern.
- Lengthen the advance-back time temporarily if stored per-cylinder retard must persist long enough to inspect.

### Boost control behaviour
- One session saw closed-loop boost ruler-flat on the dyno but overshoot 10 to 20 kPa on road and track despite hours
  of PID work, reproduced on a second car; another session's practitioner stopped using the ECU's closed loop for the
  same reason. Their workaround is a "passive" closed loop in open-loop mode: MAP as the duty table's second axis with
  5 kPa breakpoints near target, slightly less duty in cells above target and slightly more below, 0.5 to 2 % steps,
  and zero duty about 30 kPa over target as a backstop. Many tuners accept mild overshoot at modest boost on road cars;
  later firmware may differ.
- On the firmware of one recording, the derivative term snapped to zero the instant boost reached target, abruptly
  restoring duty and overshooting (`practice` session 070).
- In closed-loop mode the duty table load axis is the boost target, so the MAP-axis passive approach is for open-loop
  mode only.
- Boost status reports rpm and MAP lockouts; read it when the solenoid is or is not driving unexpectedly. A MAP
  activation above spring pressure means the system never activates.
- Solenoid plumbing on customer cars is often wrong, so first boosted runs can rise uncontrolled.

### Idle and electronic throttle
- Closed-loop idle can hide a wrong base position: switching to open loop dropped one engine from about 875 to 675 rpm.
  Check idle in open loop.
- Stalling when the clutch is pressed rolling to a stop: closed-loop idle pulled the throttle shut on overrun. Fix with
  pedal, speed and rpm-above-target lockouts.
- On drive by wire, the live throttle is base plus e-throttle target; copying the live value into the base table
  double-counts. Solenoid or stepper scale numbers entered on a DBW base table send the engine to the limiter.
- E-throttle setup mode disables safety checks; return to on before driving. A faint hum at key on, engine off, is the
  motor holding position; an option relaxes it when stalled. Closed DBW throttle reads about 0.9 % because the ECU uses
  it for idle. Some Toyota and Lexus pedals have a sub sensor that saturates before the main; set its maximum where it
  stops.
- Idle valve response is non-linear: the first 10 % of extra base position did little, then idle reached target at
  43.5 % (`practice` 8.151).
- Idle ignition throttle lockout set at 1.5 to 2 % keeps retarding during a gentle pull-away; closed-throttle readings
  wander 0.2 to 0.3 %, so set the lockout about 0.2 % above the logged closed value.

### Inputs, outputs and calibration
- MAP calibration against the onboard baro fails when the wrong MAP sensor is selected, so it doubles as a check.
  Key on, engine off: MAP should equal baro and MGP read zero.
- TPS calibration is easy to skip: one car read 99.1 % at full throttle. Sweep slowly after calibrating to find worn
  tracks.
- Digital inputs: switch to ground uses pull-up on, active low, falling edge; a switch to 12 V uses pull-up off and
  active high. A 350Z clutch switch goes to 12 V. Confirm in runtime values. A clutch switch at the bottom of travel
  activates after the clutch has released, so the engine flared from 5500 to about 6175 rpm before the cut.
- On piggyback installs where the factory ECU already biases a temperature sensor, turn off the G4+ pull-up.
- The VTEC output sits on different aux outputs by plug-in variant (about aux 5 on OBD1, aux 6 on OBD2).
- On some early firmware and some digital inputs, flex sensor fuel temperature read nonsense while ethanol content was
  fine (edge or input not supporting the decode).
- An analog wideband input is skewed by small ground offsets; predefined wideband calibrations cannot be edited. Use
  CAN, or a two-point user calibration checked against a trusted reference at two lambdas (an offset of about
  0.04 lambda was typical in one session).
- The fan output needs the rpm-zero timeout or it runs the battery flat with the ECU powered and engine off. Shift
  lights and similar outputs flicker without a short switch-off timer.

### Triggers
- The trigger 1 error counter rises when too many or too few trigger 1 teeth are seen between trigger 2 events. One to
  three at start-up sync is normal; any rise while running is not. A drift ute down about 125 kW with jagged power had
  222 errors: the cam sync edge had moved next to a crank tooth, fixed by triggering on the other edge, not by offset
  (`practice` session 095).
- The statistics window shows maxima since reset and does not refresh live; an impossible maximum rpm flags trigger
  errors.
- The built-in trigger scope captures 720 deg, is not lab grade, and is meant for cranking and idle.
- Cranking timing readings wander because few teeth are seen; confirm offset at a steady idle. Remember to re-enable
  injection after cranking tests with it off.
- `vendor-doc`: missing-tooth wheels with a poorly designed gap cause trigger errors, chiefly on high tooth counts such
  as 60-2, with reluctor sensors, and worse at high rpm.

### Rotary
- `practice` (session 043): on the G4+ trailing split values are negative for trailing after leading; a positive
  value makes the trailing plug fire before the leading, which is dangerous. Tuners from ECUs that enter split as a
  positive delay are caught by this. Confirm in the software before entering a split.
- The rotary-only limiter mode cuts fuel and spark together and is made gentle because popping can damage stock apex
  seals.

### Software, logging and CAN
- Live edits are lost at power-down unless stored, and undo only goes back to the last store. Store often; save-as to
  keep the original. Edited cells show blue until stored or cleared.
- A display sharing the serial link blocks PCLink from connecting on wire-in units; unplug it. An intermittent USB
  cable made one session drop online repeatedly; confirm the ECU is online after each store.
- Custom layouts are lost on a PCLink update unless saved by name.
- PC logs open with about 100 samples of history captured before record was pressed, marked by a dotted line; onboard
  logs have none. Only the latest PC log shows in the main view; earlier runs are in the log file manager. The record
  hotkey controls PC logging only, not onboard logging.
- Onboard logging needs configuring and verifying before the car leaves; default rates near 25 Hz with slow channels
  (coolant) near 2 Hz, triggered by rpm or a switch.
- CAN streams (ViPEC and G4+): two channels both defaulting to start bit 0 overlap and the layout turns red; a user
  transmit channel number must match its stream number; widths are in bits (some receivers use bytes); IDs show in
  decimal while other tools show hex (1000 decimal is 3E8). A receiver applies its own scaling, so a factor-of-ten
  error usually means a resolution mismatch; temperatures are often sent with an offset (plus 50 C on a 350Z).
- `vendor-doc`: a firmware update generally leaves the tune alone, but the help advises saving a copy first and having the
  tune re-checked on a dyno after any update. Training adds: read the release notes, and never update on race
  day.
- `vendor-doc`: the internal wideband can stay off until exhaust is hot, which is the normal mode; the help says to
  change that only while tuning cold start.

## Worked example

A log shows a VQ35 limiting at about 6500 rpm with the rev limit table at 6700, a GP oil-pressure limit with its safe
area at 6700, and a request to raise the limit to 7200 after a valve-train upgrade.
1. The 200 rpm control range explains limiting from 6500: cut starts at 6700 - 200.
2. Raising the main table to 7400 (so cutting starts at 7200) changes nothing, because the GP table's 6700 is now the
   lowest active limit.
3. Set the GP table's safe area to 10000 and its low-pressure cells to the protection value; then the main limit takes
   effect.
4. Log rpm, active limit, limiter status and percent cut on a full-throttle pull: a smooth cut trace with no spike past
   the value means the start cut is close to what the engine needs (`practice` sessions 036, 084, 171).

## Disputed / conflicts

- **Closed-loop boost on G4+.** Two training sessions report road overshoot they could not tune out and use passive
  MAP-axis open loop instead; the help and other training sessions set up and use the staged closed loop routinely.
  The disagreement may be firmware-dependent. Test: compare boost error on road or track logs, not the dyno, for both
  methods on the same car.
- **Onboard knock reliability.** One practitioner found it inconsistent on several cars (opinion); another trusts a
  validated setup and tunes individual cylinders from it. Both back it with audio detection when tuning.
- **Fuel cell cap.** One practitioner's tune treats 150 as the traditional cell maximum; other sources speak of a 100 %
  cap on some ECUs and aim peaks well below it. Check the field range in the software version in use.
- **MAP limit control range default.** A course lesson gives 10 kPa, a turbo session 20 kPa. Read the setting in the
  tune rather than assuming.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
