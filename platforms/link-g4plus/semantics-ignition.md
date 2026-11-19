---
id: platforms/link-g4plus/semantics-ignition
title: How Link G4+ tables behave: ignition, triggers, knock and cams
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-17
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/link-g4plus/semantics]
supersedes: []
---
# How Link G4+ tables behave: ignition, triggers, knock and cams

Part of `semantics.md`, which holds the overview, scope and sources; read it first. This file holds the ignition, triggers, knock and cams settings and how they behave.

## Why (derivation)

### Knock
- `vendor-doc`: Retard Gain is the degrees removed per percent of knock level above the threshold; Advance Delay and
  Rate set the return. The processing delay is 0.004 x rpm degrees on firmware 5.6.5 and later and 0.012 x rpm before.
  Window start, window length, retard limit and delay must all fit between the two closest firing events. Retard is
  stored in per-cylinder trim tables, and Clear I-Trim Tables decides whether it resets at power-on.

## Practical use

### Ignition
- Ignition Delay compensates for signal path delay, which grows in crank degrees with rpm and otherwise gives a slight
  retard of a few degrees. Dwell must rise when voltage falls; not all igniters limit current, so excessive dwell can be
  harmful. Maximum advance hard-caps the total after stacked trims. Spark edge is falling for most systems and rising
  for some Honda, Ford and MSD setups (`vendor-doc`, `practice` tutorial 6.2).
- Above 8 cylinders, knock control and individual cylinder trims may not work correctly; the help ties this to
  odd-fire wasted spark (see Disputed). Trailing split tables appear only with Engine Type set to Rotary.
- Fuel trims in extra compensation tables are a percent of the main table; ignition trims are degrees, and several can
  be stacked (4D to 6D compensation, `practice` tutorial 10.4).
- `vendor-doc`: the main table is rpm by load in deg BTDC (negative is ATDC), up to 22 by 20. The Ignition Table
  channel shows the raw cell; Ignition Angle shows what was delivered after every trim and 4D/5D table, so judge knock
  retard and temperature trims from Ignition Angle. Max Ignition Status on means the Maximum Advance clamp is cutting
  the sum.
- `vendor-doc`: ECT and IAT ignition trims add degrees (negative values retard) and are interpolated linearly. The 2D
  versions are tied to their sensor; the 3D versions take any axes and can serve as general trims. The help's examples
  retard when hot, from about 100 C.
- `vendor-doc`: 4D/5D ignition tables add degrees, optionally only while a condition holds (a nitrous solenoid, for
  example). A turbo engine with individual throttles may want different timing at the same MAP and rpm (200 kPa at
  5000 rpm, full throttle against half), and a 4D table on throttle can express that. Where no switching is needed, the
  help prefers the larger dual-table overlay.
- `vendor-doc`: there are three dual ignition modes. Switched chooses the second main table by an input (do not use
  Always On activation). Overlay adds the two. Interpolate mixes the two by a 0-100 ratio table (0 = table 1,
  100 = table 2, 50 = halfway) on an axis such as ethanol %, Multi Fuel blend or analog voltage.
- `vendor-doc`: dwell (ms) is set by the coil and igniter, typically 1.5-7.0 ms at normal voltage. Too short misfires;
  too long heats the coil and igniter without necessarily adding energy. Lay the table out on battery voltage (about
  7-14 V in 1 V steps) by rpm, with longer dwell at low voltage. Duty-cycle dwell is for igniters that set their own
  dwell. Inductive coils typically have a 0.4-1.0 ohm primary.
- `vendor-doc`: Spark Duration is the least time after a spark before the next dwell may begin, so dwell shortens by
  itself at high rpm when sparks crowd together (mostly with distributors); 0.5-1.0 ms is typical.
- `vendor-doc`: Ignition Delay covers edge detection, filtering, processor, output, igniter and coil delays (20-200
  microseconds each), which show up as retard that increases with rpm. With timing locked, start at 0, sweep rpm under
  a good light and raise the value until the mark holds still; most systems end up at 40-80 microseconds (see
  Disputed). It cannot correct mechanical drift such as belt stretch.
- `vendor-doc`: G4+ ignition outputs are logic level (about 20 mA at 5 V when high, low side protected to 2 A), so
  every coil needs an igniter. Spare channels can serve as plain switched aux outputs.
- `vendor-doc`: the ignition modes are wasted spark, direct, distributor, twin distributor, odd-fire wasted spark, and
  rotary leading wasted or direct. Distributor works with any cylinder count, wasted spark up to 12 (even counts only),
  and direct up to 8 with one drive per cylinder (Thunder, Xtreme, Storm 8; Fury 6; Atom, Monsoon 4). With coils, odd
  cylinder counts need direct; odd-fire wasted spark requires 720 deg triggering.
- `vendor-doc`: in wasted spark every drive fires twice per cycle on a pair of cylinders 360 crank deg apart. Ign 1 is
  cylinder 1 with its partner, and Ign 2 is the next cylinder in firing order with its partner. With single-post coils,
  split each ECU output across two igniter channels, one channel per coil.
- `vendor-doc`: with a distributor, rotor phasing bounds advance. The rotor tip should just be leaving the cap post at
  the lowest timing used (about 10 deg BTDC is typical). The point where the rotor's leading edge meets the post is the
  most advance possible before crossfire or weak spark. Misfire confined to high-advance cells may come from rotor
  phasing rather than knock.
- `vendor-doc`: Ignition Test (0 rpm only, for wiring checks) pulses a single channel at 10 Hz with 5 ms dwell.
- `vendor-doc`: transient retard is a table on TPS or MAP delta, normally by rpm. It is applied instantly on a quick
  load rise, kept for Hold Time engine cycles, then removed at Decay Rate deg per cycle; -12 deg with hold 5 and 1 deg
  per cycle is gone after 17 cycles. The Transient Ign Trim and TP Delta Max channels show it.
### Knock control
- Knock control operates only above 500 rpm. It reduces advance based on internal detection or an external unit on a
  digital input, and it is not a substitute for a correct map. Clear I-Trim Tables at power-on (the common choice)
  starts each drive fully advanced; with it off, the stored retard is kept and must then be right. Window Start is
  measured after the ignition event.
- Filter: a narrowband centred on the bore-derived frequency is preferred for signal to noise (examples 6 kHz on an
  RB25, about 7 kHz on a 4G63); the wide 4 to 10 kHz option fits a flat-response sensor yet lets more noise in.
- Threshold (target) table: at its maximum of 1000 the system is armed but inert. Log raw per-cylinder levels on
  knock-free low-timing pulls and set the threshold 20 to 30 % above that floor. Set overall gain so knock-free noise
  near the rev limit at full throttle sits mid-scale (see Disputed). Per-cylinder gain can equalise cylinders that read
  loud on a shared sensor (for example 0.8 on one).
- Typical authority in the sources: retard limit 4 to 6 deg, return after 0.5 to 2.5 s knock-free at 0.5 to 5 deg/s,
  and lockouts below some rpm and throttle. Needing more than about 5 deg of retard means the main table is wrong.
  Above the help's rpm limit for the cylinder count, detection can be wrong; set RPM High Lockout below it.
- `vendor-doc`: how retard is booked per cylinder depends on ignition mode. Direct spark keeps cylinders apart. Wasted
  spark detects per pair and credits it to the pair's first cylinder in firing order. Distributor uses one table and
  twin distributor two groups. Rotary leading wasted cannot tell rotors apart; leading direct can. Sharing trim tables
  groups cylinders (all together, per bank, or front and rear).
- `vendor-doc`: each event removes Retard Gain x the percentage by which the level sits above threshold (gain 1.0 at
  1 % over gives 1 deg; gain 0.5 at 20 % over gives 10 deg). Ign Retard Limit caps the total in case the threshold is
  set too low. Retard is written into that cylinder's trim table at the rpm and load where it happened; online, those
  cells are shown blue.
- `vendor-doc`: window budget (5.6.5 on): the sum of Window Start, Window Length, Ign Retard Limit and processing delay
  (0.004 x rpm deg) must stay under the smallest angle between sparks. A direct-spark V8 (90 deg apart) at 8000 rpm
  carries 32 deg of delay; with a 40 deg length and 10 deg retard limit, the start can be at most 7 deg. The help's
  permitted totals are 120 deg to 15000 rpm for four cylinders, and for eight cylinders 50 deg up to 10000 rpm or
  66 deg up to 6000 rpm. Through 5.6.4 the delay is three times as long (an eight-cylinder total of 48 deg holds only
  to 3500 rpm). Window Start counts from the spark: a 15 deg BTDC spark with a 10 deg start opens the window at 5 deg
  BTDC.
- `vendor-doc`: filter options are off (testing only), 4-10 kHz or 10-16 kHz wide band, or narrow band at a set
  frequency. The bore estimate is kHz = 1800 / (pi x bore in mm), about 6.7 kHz for 86 mm. The help suggests narrow
  band at 6 kHz with Bosch broadband sensors (EJ20/EJ25, 4G63, SR20DET, 3S-GTE) and with 1UZ-FE factory sensors;
  6 or 7 kHz for an RB26 on Bosch; and 13 kHz for factory resonant sensors (Evo 6 on, WRX V7 on). Choose for the sensor
  as well as the bore (see Disputed).
- `vendor-doc`: Gain Channel scales the level numbers (lower it if levels reach full scale; 0 removes the signal).
  Cylinders far from a central sensor read lower (1 and 4 on an inline four); gain per allocation (neutral 1.0,
  half 0.5, double 2.0) evens them out on a knock-free free-rev. The target table (0-1000, speed by load) stands for
  acceptable mechanical noise, including valvetrain; the help puts each cell about 20 % over the loudest knock-free
  cylinder at that point.
- `vendor-doc`: lockouts are under 500 rpm, low and high rpm limits, low throttle, fast throttle movement, launch
  armed, and a start-up delay while the signal settles. Knock retard is kept apart from the individual cylinder
  ignition trim channels and does not show in them.
- `vendor-doc`: per-cylinder counters count threshold crossings, and the global counter is their sum; levels exist per
  cylinder and combined. One cylinder counting alone points at that cylinder (a lean injector or hot spot); all of them
  counting together points at noise or a general fault.
- `vendor-doc`: by default trims are cleared at power-off, and switching knock mode off and on clears them as well.
  With clearing disabled they keep their last stored values.
- `vendor-doc`: Atom and Monsoon accept external knock modules only; other G4+ units have Knock 1/2 inputs (Storm
  shares the An Volt 2 / DI 4 pins). One-terminal sensors use shielded single-core cable and earth through the block;
  two-terminal sensors use shielded twin-core with the ground run back to the ECU. A 0-5 V signal on a Knock channel is
  display-only (useful when setting gain) and does not feed control.
- `vendor-doc`: an external module (a KnockBlock with low polarity, e.g.) needs one aux output configured as a knock
  window to gate it per cylinder (live only above 500 rpm with knock mode on), plus a digital or 0-5 V return input.
- `vendor-doc`: Knock Audio sends the amplifier output to a waterfall spectrum. With safe timing at about 1500-2000
  rpm, set gain so peaks fall between the first and second graticule lines. A single thin band means a resonant
  (narrow-band) sensor, and its frequency can be read off; a wide spread of colour means a wide-band sensor.
  Second-harmonic types can lie beyond 10 kHz, so widen the range. The example spectra show knock energy at about
  5-7 kHz.
### Cam control, VVT and VTEC
- Use a preset mode where one exists. For inlet cams the most retarded position is the least aggressive; for exhaust
  cams the most advanced is (`vendor-doc`). Most VVT solenoids are driven much faster than boost or idle
  valves (250 Hz on a VQ35 in training), though BMW VANOS on S52/S54 runs 50 Hz (see Disputed).
- Targets are advance from the cam's rest position found by the cam angle test, not a spec-sheet centreline (the test
  found about 158 deg ATDC rest on a K24). Increase test pulse count until readings settle; enter the lowest stable
  angle as the offset; turn the test off.
- VTEC: drive the solenoid from a GP output with AND conditions (rpm, throttle, coolant); use dual-table mode keyed to
  that output, not overlay, so table 1 is low cam and table 2 high cam. Dual fuel tables matter most; dual ignition is
  optional since 2 to 3 deg error still sits near MBT. Tune each table past the switch point so moving the switch does
  not create fuel errors. A cam phaser took roughly 0.1 s per 10 deg, so lead the VTC target ahead of the switch.
- Changes in required fuel when the cam is moved measure the cam's effect on filling, which works off a chassis dyno
  by comparing logged corrections (`practice` Civic part 5).
- `vendor-doc`: cam solenoids run only on Aux 1-4, switched on the low side with the other side on ignition-switched
  power, typically at 250-300 Hz (see Disputed). Cam position inputs work only on DI 1-4 (about 500 Hz max). Setup is
  simplest with pairs: inlet (or inlet LH) DI1/Aux1, inlet RH DI2/Aux2, exhaust (or exhaust LH) DI3/Aux3, exhaust RH
  DI4/Aux4. A cam sensor that also gives sync goes to Trigger 2 and is set in the Trig 2 VVT menu.
- `vendor-doc`: reluctor cam sensors must use the falling edge, while Hall sensors can use either; the wrong edge
  shifts the offset. The offset is the crank degrees from TDC to the first cam signal with the cam fully retarded.
- `vendor-doc`: sign convention: the inlet target is advance from fully retarded (0 = retarded, positive = advance),
  and the exhaust target counts from fully advanced (0 = advanced, negative = retard). There are as many as three
  target tables each for inlet and exhaust, with one of each active. Centreline display shows targets as lobe
  centreline angles and needs centrelines measured on the engine (see Disputed for direction).
- `vendor-doc`: VVT is off at zero rpm, on a cam signal error, during the cam test and below its rpm and ECT lockouts;
  inlet cams then park fully retarded and exhaust cams fully advanced. Lockouts usually sit at 500-1500 rpm (VVT works
  at idle with 500, not with 1500) and 20-50 C, because low rpm means little oil pressure and cold oil is thick. Some
  engines cannot hold VVT below about 1500 rpm.
- `vendor-doc`: closed-loop PID frees cam position from dependence on oil temperature and pressure. One PID set can
  serve several cams that are still controlled separately. ECT-indexed minimum and maximum duty clamp tables bound the
  solenoid, because required duty shifts with oil viscosity. Position filtering evens out belt slack and speed ripple
  but adds loop delay; the help suggests 4-6.
- `vendor-doc`: User Defined VVT only fits an advancing inlet plus a retarding exhaust, each cam on one solenoid, and
  it always needs its own PID tuning. Setup: set both target tables to zero; run Cam Angle Test, raising Test Pulse
  Count until the angles settle with none repeated; sort them; use the lowest value above 0.0 as the offset. Enter each
  tooth as its angle less the offset (the first is always 0), rounded to likely design multiples of 30 or 45 deg. Set
  Cam Tooth Tolerance to the smallest tooth gap less 15 deg, and 70 deg at most. Cam Angle X reports the crank angle
  after TDC at which each cam pulse arrives.
### Triggers
A valid tooth count divides evenly into 360, and on a missing-tooth wheel it counts the teeth as if none were missing.
Arming threshold and filtering are advanced features; start at the lowest filtering, since filtering removes
information. A preset OEM mode configures both inputs, but sensor type, pull-up (on for Hall or optical), edge and
sync mode still need checking. Timing must be calibrated with a timing light after setup: lock timing, set the offset
with the engine idling steadily (two lessons used about 1500 rpm; see Disputed for the help's speed), then raise rpm
and adjust Ignition Delay until the mark stops drifting
(1 to 2 deg of drift by 6000 rpm is normal; large drift suggests reluctor polarity). An RB25 with a 24-tooth disc sat
at -344 deg and needed no delay change up to 5000 rpm (`practice` RB25 part 2).
- `vendor-doc`: raising Trigger Offset advances ignition and injection together. For a first estimate on a
  missing-tooth wheel, take the angle from the first tooth after the gap to the sensor with cylinder 1 at TDC. It is
  negative when the gap has already passed the sensor (40 deg past gives -40) and positive when it is still to come
  (60 deg away gives +60). Sync can land a revolution out; if the spark would come with the valves open, add or
  subtract 360 (-40 to 320, 60 to -300). Always confirm with a timing light.
- `vendor-doc`: up to 60 teeth are supported; a count that does not divide 360 (a 32-tooth wheel, 11.25 deg) spaces
  cylinder timing unevenly.
- `vendor-doc`: crank position always comes from Trigger 1 and firing-order position from Trigger 2. Sync Mode None
  or Crank Pulse 1x gives 360 deg position only, which suits rotary, two-stroke, or four-stroke on group fuel with a
  distributor or wasted spark. Cam Pulse 1x or Cam Level gives the 720 deg position that sequential fuel and direct
  spark need, so Trigger 2 must turn at cam speed. On a missing-tooth wheel Crank Pulse 1x adds nothing over None.
- `vendor-doc`: Cam Level needs multi-tooth/missing, not plain multi-tooth. The cam level is sampled at the first crank
  tooth after the gap (low = 0 deg plus offset, high = 360 deg plus offset), so a multi-tooth cam wheel works provided
  the level at that tooth flips every revolution.
- `vendor-doc`: sync edge placement: in multi-tooth mode the Trigger 2 edge must lie in the middle half of the space
  between two Trigger 1 edges. In multi-tooth/missing, keep it out of the gap and at least 30 crank deg from the first
  tooth after it. An edge close to a crank edge can drift into the wrong interval with cam phasing or belt stretch.
- `vendor-doc`: above Trig 2 RPM Lockout the ECU ignores Trigger 2 for sync, being already synchronised. Without
  trigger errors, leave it above the operating range (12000 rpm in the help); about 3000 rpm fixes some error cases.
- `vendor-doc`: Arming Threshold (reluctor) is a table in 1000 rpm steps giving the voltage the signal must pass before
  the ECU looks for a falling edge. Sensor output is small when cranking and rises with speed, so the table starts low
  and climbs. Set each cell to half the positive peak of the weakest tooth at that speed (a 5 V peak gives 2.5 V),
  taken from a scope or trigger scope. Fill the 0 rpm cell from a cranking capture with fuel and spark disabled. The
  Trigger 1 Arming channel shows the threshold in use.
- `vendor-doc`: reluctor polarity must be positive as the tooth approaches and negative as it leaves. Reversed
  polarity gives timing error and rough running, so check it on a scope. Hall and optical sensors need a supply (8 V
  or 5 V; 8 V or 12 V kills many 5 V parts) and normally pull-up on.
- `vendor-doc`: Trigger Priority sets which input is serviced first if edges coincide. Trigger 1 is the norm, and
  swapping is worth a try for persistent sync errors from coinciding edges. RPM Filtering averages speed over 1-4
  TDC events. Keep the default of 1 unless a one- or two-cylinder engine's speed swings too much within the cycle to
  tune. It smooths only the rpm used by tables and settings, not event scheduling (5.0.2 notes).
- `vendor-doc`: Custom TDC Points (off by default) serve odd-fire engines. Each TDC is entered as an engine position in
  firing order (0-720 deg four-stroke, 0-360 deg two-stroke), beginning with the first cylinder to fire.
- `vendor-doc`: in Nissan 360 optical mode each of the 360 slots gives position, and the ECU learns the widest sync
  slot, which varies by CAS. With injection off, Test ECCS Sync plus about 4 s of cranking should give both trigger
  signals, ECCS Sync Yes and a widest-slot value, typically 5-25. Zero after 10 s means a wiring or CAS fault. Low Res
  mode is for wild cams or light flywheels, where CAS speed varies within a revolution.
### Rotary
- `vendor-doc`: 1-4 rotors only. Use Rotary Leading Direct or Rotary Leading Wasted ignition through igniters. Put the
  primaries on the first drives and the secondaries after them, as Sequential/Staged, each set with its own dead time;
  sequential on 3 or 4 rotors needs Xtreme, Fury or Thunder. See `quirks-ignition.md` for the trailing split sign.
- `vendor-doc`: timing check: with injection off, set trailing split to -20 around the test area, lock timing at 0,
  put the light on the front trailing lead and adjust the offset to the 20 deg ATDC mark. Then restore injection, store
  without the temporary split, and repeat while running near 2000 rpm. Rotaries idle poorly at TDC timing.
- `vendor-doc`: the metering oil pump stepper sits on Aux 5-8, with position feedback calibrated 0-100 % (about
  0.8-0.9 V closed and 4-4.4 V open, across two topics). The 3D oil flow table is set per build. If the stepper cannot
  reach target, a fault holds the engine to 2000 rpm. Confirm OilP Position follows the table before running.

## Disputed / conflicts

- **Knock retard gain and authority.** The help and tutorial use 0.5 deg per percent; one session used 0.2, one
  practitioner 0.25. Return delay ranges from 0.5 s to 2.5 s and rate from 0.5 to 5 deg/s across sources.
- **Knock overall gain.** One session sets no-knock full-throttle noise at 400 to 500 of 1000, another at 500 to 600;
  both want mid-scale without saturation.
- **Knock window start.** The help measures Window Start after the ignition event and the tutorial example starts
  10 deg after spark; one practitioner describes the same default as opening 10 deg before TDC. Check the help for the
  firmware in use.
- **VVT coolant lockout.** The default had a 40 C coolant lockout; one practitioner disables it so a cold engine driven
  hard does not run parked cams against a fuel map tuned with cams active (opinion).
- **Ignition delay typical value.** The help's trigger calibration topic quotes 20-80 microseconds and its Ignition
  Delay topic 40-80. The text above uses the dedicated topic.
- **Trigger offset check speed.** Two course lessons set the offset at a steady idle of about 1500 rpm; the help's
  trigger calibration topic rechecks once running steadily at 2000-4000 rpm, because crank speed ripple spoils readings
  at low speed. Both distrust cranking readings. Test: compare the mark at idle and at 3000 rpm with Ignition Delay
  already set.
- **Knock filter on 4G63.** Training uses about 7 kHz; the help lists 6 kHz narrow band where an aftermarket Bosch
  broadband sensor is fitted, but 13 kHz for factory resonant sensors (Evo 6 onward). Probably sensor-dependent;
  confirm with Knock Audio.
- **Knock threshold margin.** Training sets it 20-30 % above the logged floor; the help sets it about 20 % above the
  loudest knock-free cylinder. These are compatible.
- **Above 8 cylinders.** Earlier text here (no source tag) applied the knock and cylinder trim problem to every
  engine over 8 cylinders; the help's Ignition Mode topic states it only for odd-fire wasted spark. Until checked,
  treat knock control and per-cylinder trims as unproven on any engine over 8 cylinders.
- **VVT centreline direction.** The help's Centre Line Control topic reads inlet centrelines ATDC and exhaust BTDC
  (examples: inlet 108 deg ATDC when fully retarded, exhaust 109 deg BTDC when fully advanced); its target table topic
  says inlet BTDC and exhaust ATDC with centreline display on. Verify in software before entering targets.
- **VVT solenoid frequency.** Training says VVT solenoids run much faster than boost or idle valves (250 Hz on VQ35);
  the help agrees for most engines (250-300 Hz) but lists 50 Hz for BMW S52/S54 VANOS, below its 200 Hz idle valve
  figure.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
