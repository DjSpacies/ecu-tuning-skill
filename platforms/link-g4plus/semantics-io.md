---
id: platforms/link-g4plus/semantics-io
title: How Link G4+ tables behave: inputs, outputs, logging and CAN
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-17
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/link-g4plus/semantics]
supersedes: []
---
# How Link G4+ tables behave: inputs, outputs, logging and CAN

Part of `semantics.md`, which holds the overview, scope and sources; read it first. This file holds the inputs, outputs, logging and CAN settings and how they behave.

## Practical use

### Inputs, sensors and calibration
- `vendor-doc`: MAP calibration offsets an external sensor so that, with the engine off, it agrees with the
  factory-calibrated onboard baro; afterwards MAP and baro should match within 1 kPa. An uncorrected offset moves the
  whole tune, and the MGP axis suffers most because MGP is MAP less baro. Calibrated units let one file behave the same
  on another G4+.
- `vendor-doc`: baro is about 101 kPa at sea level. Most G4+ units carry a factory-calibrated internal baro sensor. Fit
  an external one if the ECU lacks it or is sealed from the atmosphere (waterproof units use the Marine calibration).
  The Altitude channel assumes 101.3 kPa at sea level, so weather alone can move it by up to about 200 m either way; it
  is not a survey altitude.
- `vendor-doc`: the TPS must be a full-range potentiometer on the throttle shaft, ideally about 0.5 to 4.5 V in either
  direction (the ECU detects the direction). 0 V and 5 V count as faults, so travel must stop short of the electrical
  ends. Idle and WOT switches are no substitute, because the analog value feeds accel enrichment (where the help
  prefers TPS to MAP), overrun cut, idle, anti-lag and some boost strategies even when fuel runs on MAP.
- `vendor-doc`: every analog channel has Error Low and Error High limits (usually 0.05 V / 4.95 V); entering 0.00 V or
  5.00 V disables that side. If the signal stays outside the window for over 1 s, the ECU stores a code, lights the CEL
  and substitutes the Error Value, returning to the live value once the signal is back inside. Choose error values that
  leave the engine safer (less timing; for ECT, a temperature above fan-on so the fan runs). A dedicated MAP, TPS, ECT
  or IAT fault always comes with a generic analog fault on the same pin.
- `vendor-doc`: an open thermistor circuit reads high voltage and an open voltage sensor reads low. A channel stuck at
  0 V or 5 V where it should not be points to an open circuit or a short to ground or 5 V.
- `vendor-doc`: An Temp and An Volt differ only in the 1 kohm internal pull-up to 5 V on the temperature channels. A
  0-5 V sensor (a pyrometer amplifier, for example) on a temperature channel reads wrong. A thermistor on a volt
  channel needs an external 1 kohm pull-up to 5 V, or the factory ECU's pull-up when piggybacking. On most models (not
  Atom or Monsoon), An Temp 1 and 2 offer other pull-ups (1 to 47 kohm) for high-resistance sensors, or none.
- `vendor-doc`: with the 1 kohm pull-up, an NTC sensor's voltage drops as it warms (standard Bosch: 20 C about 3.6 V /
  about 2.5 kohm, 100 C about 0.8 V / under 200 ohm), while a PTC sensor's voltage climbs. A temperature that moves the
  wrong way during warm-up means the wrong sensor type is selected.
- `vendor-doc`: custom calibrations 1 to 3 use evenly spaced outputs (ohms for thermistors, volts otherwise) and fail
  if the first two input cells match. Calibrations 4 to 6 are two-point linear (the wideband example puts 0 V at 9.0
  AFR and 5 V at 19.0). Calibrations 7 to 10 accept unevenly spaced points. Link-branded MAP sensor calibrations are
  two-point linear: for example 2.5 bar = 20 to 250 kPa over 0.2 to 4.9 V, 4 bar = 20 to 400 kPa over 0.2 to 4.8 V,
  and 1.15 bar = 15 to 115 kPa over 0.2 to 4.7 V.
- `vendor-doc`: calibrate fuel, oil and exhaust pressure in kPa and convert units at the dash. Sensors rated for air
  are not suitable for fuel, oil or water.
- `vendor-doc`: MAP plumbing should have a bore of 3 mm or more and come from a common plenum after the throttle (the
  regulator reference is the usual choice). Never take it from one runner, and never share it with a boost gauge or
  blow-off valve. Mount the sensor above the manifold so condensation drains. A shared or pulsing source gives a noisy,
  lagging load signal.
- `vendor-doc`: digital inputs have an optional 4.7 kohm pull-up to 12 V; they read low under 1 V and high over 2 V.
  Only DI 1 to 4 can read cam position. DI 1 to 6 accept frequency signals (wheel speed, digital knock) up to 500 Hz.
  DI 7 and up are for switches only.
- `vendor-doc`: wheel speed calibration is in pulses per 100 m (170 to 280 is typical). Get it from a drive at known
  speed, or calculate it as 31.83 x teeth / wheel diameter (m). With only a gearbox VSS, set it as driven speed and
  turn non-driven speed off, which removes slip. Driven Wheel Speed Correction (%) allows for tyre size. The slip
  filter ranges from 0 (off) to 8.
- `vendor-doc`: clutch or converter slip, in %, is 100 x (engine rpm / input shaft rpm - 1). It is zero when the
  speeds match, 100 % with the engine at twice shaft speed, and -50 % at half. Input shaft rpm = DI Hz x 60 / teeth,
  and max rpm x teeth / 60 must stay under 500 Hz (5 teeth up to 6000 rpm, 4 up to 7500, 3 up to 10000).
- `vendor-doc`: gear detection has two modes. RPM/Speed mode, for manual gearboxes only, divides engine rpm by the
  driven-speed frequency and matches the result against stored ratios; when nothing matches it reads neutral or
  clutch in. Analog mode uses a voltage per gear with a tolerance (1.5 V plus or minus 0.2 V finds gear 1 from 1.3 to
  1.7 V). The stored ratios are in rpm per Hz, not gearbox ratios; read them from Gear Ratio Calc in each gear.
  Learning needs over about 15 km/h and a ratio steady for 3 s, with a 12 s timeout. In Driving Gear and every
  per-gear function depend on this setup.
### Outputs and logic
- `vendor-doc`: aux outputs switch the low side (with a 1.5 kohm internal pull-up) at 2 A each, so a directly driven
  load must be over about 7 ohm; heavier loads need a relay. PWM frequency ceilings are about 4000 Hz on aux 1 to 4
  (VVT needs these), 300 Hz on aux 5 to 8, and 20 kHz on some higher channels. 3-wire ISC solenoids use aux 1 and 2,
  steppers aux 5 to 8, and the internal e-throttle motor aux 9/10. Check the model's allocation chart before placing a
  fast solenoid.
- `vendor-doc`: high-side drive on aux 5 to 8 (Storm Black, Xtreme, Fury, Thunder) is for single-wire solenoids
  grounded through the body, such as Honda VTEC. It supplies 0.5 A maximum, so the coil must be about 30 ohm or more.
  High-resistance loads do not suit it, because the permanent pull-up keeps them partly on.
- `vendor-doc`: spare injection and ignition channels can serve as aux outputs, but if the injection or ignition mode
  needs that channel, the mode takes priority without any warning. These channels have no flywheel diode, so a fast
  solenoid such as an ISC valve needs an external one.
- `vendor-doc`: PWM outputs are active low, so 10 % duty means the output is grounded for 10 % of the time. The pump
  speed output is fixed at 80 Hz with three duty steps (see Fuel system and pump control in `semantics-fuel.md`).
- `vendor-doc`: shared aux output tables take the units of the assigned function (cam degrees for VVT, duty for GP
  PWM). While a GP PWM output is inactive, its active-cell marker sits at the top left; this means inactive, not an
  operating point.
- `vendor-doc`: a GP output takes up to three conditions (two on aux fuel and ignition channels), joined by AND/OR with
  brackets, plus a switch-off timer. The hysteresis pattern is (this output on AND rpm above the off point) OR rpm
  above the on point; for example, on at 4000 rpm and off at 2000.
- `vendor-doc`: special conditions such as RPM, MAP, speed, launch and GP limit active, or In Driving Gear, count as
  true while active if the value is 1, and true while inactive if it is 0. The value is ignored for Anti-Lag Active,
  Cyclic Idle Active and Engine Limits. Engine Limits is true while any RPM, MAP, speed or GP RPM limit is acting.
- `vendor-doc`: four GP timers count in 2 ms steps up to 60 s and can serve as axes or conditions; outputs they drive
  may lag by up to about 50 ms. When a timer sets the on period, set the output's own switch-off timer to zero. Aux
  and virtual aux states can be a table axis, so the table jumps rows when the state changes (for example a GP RPM
  limit keyed on a virtual aux as a limp mode). Virtual auxes read OFF, ON or FAULT.
- `vendor-doc`: the speedo output is source frequency x multiplier + offset, with a maximum. A speedo showing 80 at a
  true 100 needs 1.25; a CAN wheel speed at ten times actual needs 0.1. The tacho output is a low-level 0-12 V pulse
  per firing and cannot drive a coil-negative tacho. Aux 5 to 8, at 300 Hz, may be too slow for a V8 tacho over about
  4500 rpm, while aux 1 to 4 reach 4000 Hz.
- `vendor-doc`: shift light duty ramps over a per-gear rpm span that ends at the shift rpm (neutral uses gear 1, and
  the function needs gear detection). About 10 Hz flickers, higher frequencies dim the light, and going beyond 50 Hz
  gains nothing.
### Other outputs
- `vendor-doc`: canister purge logic is fixed: it is active only with ECT over 50 C, MAP under 90 kPa and rpm over
  1800.
- `vendor-doc`: Subaru TGVs close on cold starts below 65 C and open on throttle movement or above 65 C; they are
  always open over 4000 rpm (feedback about 4.2 V closed, 0.4 V open). With the TGVs closed the engine runs very rich,
  so remove fuel with an overlay on the TGV position channel.
- `vendor-doc`: intercooler spray cycles the pump at a low rate and duty (typically a 5 to 10 s period, 25 to 50 %
  duty, and a 400 rpm lockout).
- `vendor-doc`: turbo speed needs an interface whose output stays below 500 Hz at full speed; the calibration value is
  6000 x number of blades / divider.
- `vendor-doc`: the engine fan switches on at its ECT threshold and off after the hysteresis (on at 95 C with 5 C
  hysteresis, it stays on until under 90 C). It can optionally switch on 1 s after the A/C clutch.
### Power, hold power and ECU health
- `vendor-doc`: the supply must stay over 7 V at all times, cranking included. A deeper dip resets the ECU and stops
  the engine, and the Under Voltage status comes on under 7 V. Trigger the main relay from key-on, not ACC, which
  usually drops out during cranking.
- `vendor-doc`: the 5 V sensor supply should read about 4.9 to 5.1 V; anything outside that is a fault. Ratiometric
  sensors scale from it, so a sagging rail moves MAP, TPS and every other sensor on it together; check all the sensors
  that share it. The 8 V supply should sit near 8 V.
- `vendor-doc`: aux 9/10 on Xtreme, Fury and Force GDI, and aux 17 to 20 on Thunder, need their supply pin powered
  near battery voltage, or the outputs and the e-throttle self-checks fail. If the aux 11 to 16 driver status goes to
  over-temperature and then thermal shutdown, the outputs are overloaded and have switched off.
- `vendor-doc`: hold power (ignition switch on a DI, main relay on an aux) keeps the ECU alive after key-off while the
  engine turns, a stepper resets or the keep-alive time runs. Key-off ends fuel and spark. With Kill Until Stalled =
  No the engine may restart if the key returns while coasting; with Yes it waits for zero rpm. A peak-and-hold
  injector drive cannot act as a hold-power output.
- `vendor-doc`: a Data Count Error that keeps rising after a power cycle, a lasting Dataflash checksum ERROR, or
  logging chip errors are internal ECU faults for the dealer, not tune problems. The recommended internal temperature
  is -20 C up to 70 C.
- `vendor-doc`: counters saturate. Engine Cycle Count stops at 60000 cycles (about 10 min at 6000 rpm) and Engine
  Running Time at 60000 s (16 h 40 min), so anything tied to run time is pinned after that. ECU statistics (counters,
  maxima, run times) persist through key-off until cleared, either as a whole or per item, so they keep a record of
  past over-limit events.
- `vendor-doc`: table memory is finite. Less-used functions draw on a pool of slots as they are enabled: 20 on Atom,
  Monsoon and Storm, and 30 on Xtreme, Fury, Thunder and Force GDI. Table Allocation Status ERROR means the pool is
  full.
### Configuration limits by model
- `vendor-doc`: set the engine type, cylinder count, firing order (cylinder 1 first) and TDC points before anything
  else. Sequential staged injection reaches 4 cylinders or rotors; beyond that it is group staged. Wasted spark needs
  an even count (2 to 12) and direct spark stops at 8. 9 and 12 cylinders are limited to a distributor (or wasted
  spark for 12), and rotary engines use leading wasted or leading direct.
- `vendor-doc`: model differences: the Atom has no VVT, launch, anti-lag or closed-loop boost. Storm and Storm Black
  get e-throttle only through an external module. Only Xtreme, Fury and Thunder have peak-and-hold drives. Fury (1),
  Thunder (2) and Force GDI (1) have internal wideband control. Closed-loop lambda Auto and dual closed loop exist from
  Xtreme up. Monsoon and Storm carry a 4 bar onboard MAP. A function missing from a tune may be a model limit.
### Tables
- `vendor-doc`: breakpoints are cell centres. A cell's value applies exactly only at its centre and everything between
  centres is interpolated, so the highlighted cell is merely the one with the most weight. Setting an axis to None
  turns a 3D table into a row or column, and setting both to None makes it a single value. Axis changes take effect
  only after Apply.
- `vendor-doc`: logged crosshairs over a table need a log from the same configuration that contains the table's axis
  channels. Tuned-cell markers keep Quick Tune off finished cells. Compare Base Map overlays two maps and highlights the
  cells and settings that differ: save a copy at the start of a session to audit changes, or use it to check whether a
  customer's map was altered.
### Logging
- `vendor-doc`: onboard logging is independent of PC logging. It records only while every condition is met (IO, plus
  rpm, TPS and MAP over their settings), plus an off-delay. Limits are 2500 samples/s in total and 100 Hz per channel;
  100 parameters on 5.5.5 and later (PCLink warns when the total is exceeded) and 25 on 5.5.4 and earlier. 25-channel
  logging has been free since 5.4.1. Memory is circular, so at 100 % the oldest data is overwritten ("Memory Full -
  Overwriting" is normal); download before an event is lost.
- `vendor-doc`: rough onboard capacity: 25 channels at 100 Hz last about 14 min, 10 at 50 Hz last 1 h 8 min, and one
  at 0.5 Hz lasts 6 h 48 min. Log fast things (knock, lambda, rpm in transients) at a fast rate and temperatures slowly.
- `vendor-doc`: PC logging over USB at 625k baud manages about 65 Hz on a good PC (fall back to 250k if it drops out),
  and the requested rate is capped at the link rate. With "save unchanged points" off, only changes are kept.
- `vendor-doc`: an XY plot of rpm against MGP, coloured by lambda and drawn as points only, makes a scatter mixture map
  from a log. A MAP histogram coloured by AFR band is a quick screen: lean colours at low MAP are normal cruise, but in
  the high-MAP bars they flag a load area to investigate.
### CAN, serial and OBD
- `vendor-doc`: CAN carries the ECU's internal integer, and the shown value = internal x resolution + offset. Offsets:
  ignition angle -100 at 0.1 deg resolution (24.1 deg is sent as 1241); MGP -100 in kPa; ECT, IAT, oil and ECU
  temperature -50 in 1 C steps; knock trim -20 at 0.1 deg. Values without an offset: MAP, oil and fuel pressure in
  kPa; baro at 0.1 kPa; lambda at 0.001; TP, AP and duty at 0.1 %; battery at 0.01 V; wheel speed at 0.1 km/h; pulse
  width at 0.001 ms; knock level in fives. Status values are 0 = off and 1 = active (multiplier and divider 1, offset
  0).
- `vendor-doc`: on serial and CAN, exhaust cam position uses a negative scale: exhaust runs 0 to -60 deg against inlet
  0 to +60. Retard therefore reads negative on the display but travels as a positive number on CAN.
- `vendor-doc`: there are at most two user CAN modules. A stream is one or more frames sharing one ID, and each
  parameter has a start bit, bit width, byte order, sign, multiplier, divider and offset. A user stream is either
  transmit or receive, never both. Only IDs above zero are allowed, and some parameters cannot be received. CAN edits
  need Apply plus Store. To scale an incoming OEM value, tabulate raw bus values against the wanted internal value at a
  few points, including zero: ABS wheel speeds in 0.01 km/h going into the 0.1 km/h internal value need multiplier 1,
  divider 10 and offset 0.
- `vendor-doc`: OBD on CAN (ISO 15765-4 style) uses one module. Scan tools usually want 250 or 500 kbit/s, which sets
  the whole bus to that rate. Mode 01 covers closed-loop status, short and long trims per bank, commanded lambda, MAP,
  rpm, cylinder 1 timing, ethanol and EGTs, so trims can be logged without PCLink.
- `vendor-doc`: the long serial stream adds per-cylinder knock level and count for up to 8 cylinders. Its limits
  bitfield distinguishes rpm, MAP and speed limits, the max-ignition clamp, voltage limits, overrun cut, launch, and
  the analog-input limit. Its trigger bits tell a missing sensor signal apart from a sync fault. Query each analog
  channel's units and apply that unit's scaling instead of assuming it.
### Tools
Quick Tune adjusts the main fuel table only, never ignition, and the help says it assists rather than replaces a
professional tuner. Tune ignition and boost control before using it. Quick Trim and closed-loop lambda are separate
functions. Mixture Map and Quick Trim need the fuel and target tables to have matching load sources set, or a load
value entered. Mixture Map gives each cell its average actual, target, sample count and error, and can apply a
correction. Closed-loop lambda must be off for Quick Tune, which has lockouts for coolant, load and rpm. "Load Centre
Tolerance" and "RPM Centre Tolerance" decide when a cell counts as centred.
- Settings used in one session: the least filtering that removes jitter, a precision band of about 0.01 lambda, about
  1 s in the cell centre within about 10 % of the cell spacing, a minimum-load lockout so overrun cut is not
  "corrected", and a capped number of attempts (two or three usually converge). Tune-ahead copies a tuned value into
  the next cell up; add 2.5 to 5 % so the untuned cell arrives rich (`practice` session 082).
- `vendor-doc`: Quick Tune adjusts a cell only when rpm and load are inside the centre tolerances and lockouts, ECT is
  above its lockout, and the mixture has been steady for the time-in-centre; a filter of 1 means no damping. The help's
  examples: an rpm lower lockout of about 1000 rpm; a load lower lockout of about -80 kPa MGP (20 kPa MAP) so overrun
  is left alone; an ECT lockout above the point where warm-up enrichment reaches zero; a precision of 0.05 lambda (see
  `semantics-fuel.md`, Disputed); and 1 to 3 tries per cell.
- `vendor-doc`: Tune Ahead with a trim pre-fills the cells to the right and below with stepped-up values (50 with 5 %
  becomes 52.5, 55, 57.5), so an untuned neighbour starts rich; it writes only where the new value is above the stored
  one. Work one rpm column at a time up the load axis, starting at low rpm and load.
- `vendor-doc`: Mixture Map filters are a minimum sample count, an active zone (for example within 50 % of
  centre-to-edge), condition filters (TPS above 15 %, for example) and transient filters (TPS rate under 50 %/s). They
  matter because samples at cell edges also count for the neighbours, and transient samples carry lag and enrichment.
  Correct one or two rows or columns, relog the same area, move on, and store at the end. An empty map usually means
  the PC log list lacks a needed channel.

## Disputed / conflicts

- **IAT sensor position.** The help's charge temperature topic warns that a sensor upstream of the throttle may
  misrepresent the charge, puts a fast, exposed sensor ideally in the manifold, and notes that heat soak there raises
  charge temperature. Its IAT sensor topic wants the sensor just ahead of the throttle body (after the compressor and
  intercooler), away from manifold heat soak, and fast on every forced-induction engine. Several plug-in pages steer
  away from MAF and airbox sensors toward a manifold or pre-throttle sensor. The blend table absorbs either position,
  but a table tuned for one position does not transfer to the other.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
