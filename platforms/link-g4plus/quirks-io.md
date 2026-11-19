---
id: platforms/link-g4plus/quirks-io
title: Link G4+ quirks: inputs, outputs, logging and CAN
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-17
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/link-g4plus/quirks]
supersedes: []
---
# Link G4+ quirks: inputs, outputs, logging and CAN

Part of `quirks.md`, which holds the overview, scope and sources; read it first. This file holds the inputs, outputs, logging and CAN gotchas and workarounds.

## Practical use

### Adapter and file facts
- `sample-observed`: load axes in the samples are often gauge pressure (MGP), running to -85 kPa, while MAP is
  absolute. Check which one a table uses before reading a value across. In the training sessions the MAP gauge axis is
  shown inverted by default (`practice` session 294).
- `sample-observed`: most samples use Traditional mode (34 of 44 tunes with the field), 9 use Modelled and 1 uses
  Multi Fuel. Do not treat a fuel table number as VE without checking the mode.
- `sample-observed`: wideband inputs are named by the tuner (`An V2 - WideBand`), and one sample logged a blank unit
  with AFR-scale values. The adapter flags its conversion.
- `sample-observed`: the first sample of a log can be all zeros.
- `sample-observed`: one vendor tune has character references in a label field that XML 1.0 rejects. The parser
  replaces them with spaces, and only in that field.
- `re-derived`: the same name can map to several DataIds across generations (`Fuel Table1 G4`, `FuelTable1`,
  `Fuel Table2`). `tables.yaml` lists only the ids seen in G4+ tunes.
- `re-derived`: tables other than fuel, ignition and lambda target live in generic allocation slots (`G4 Table 1` to
  `12`, about 40 ids). What a slot holds depends on the tune's allocation, so boost tables have no fixed id and are not
  parsed. Unused second tables have flat filler axes and are skipped. Tuners work within a fixed budget of 3D tables
  (30 on one unit) and save slots by using 2D tables or gear trims where full 3D control is not needed
  (`practice` open-loop boost).
- `sample-observed`: the 45 tunes carry RPM and MAP limits as 18-point arrays that are lower when cold (rpm_limit is
  sometimes 4000 to 4500 for the first few points).
- `vendor-doc`: fuel table load and equation load are separate settings. The table's axis does not tell you how the
  equation estimates air charge.
### Tables that arrive with junk
- A newly enabled table (second VE, second target, flex ignition, boost tables) contains whatever was in memory. In
  one demo a fresh second target table held 0.755 lambda below 220 kPa. Inspect every newly enabled table and copy the
  first table across before tuning.
- Switching cranking or post-start enrichment from 2D to 3D wipes the values. Copy them out first and paste them into
  the 0 % blend row.
- Export and import carry the axis breakpoints, but copy and paste carries cell values only, so the axes must already
  match.
- Base files can hold dangerous values. A wastegate duty table at 100 % requests maximum boost, and warm-up enrichment
  cells near operating temperature (with throttle on the second axis) can add fuel at light throttle on a warm engine.
  Zero the warm-up cells from about 60 C upward before tuning the main table (`practice` 8.148, 8.152).
- Boost trim tables (IAT, ECT, gear) can hold odd values, and they interpolate between breakpoints: a 100 % cut at
  110 C already removes about half the duty at 105 C (`practice` session 131). Keep the trims at zero across the
  normal range.
- In closed-loop boost mode the base duty table defaults to throttle by rpm axes. Change its axes to boost target by
  rpm.
- The charge temperature approximation table has fixed axes on G4+ (rpm by MGP), so an NA engine still has boost rows.
  Copy the 0 kPa row into them.
- A factory-reset unit has injection and ignition disabled and generic settings (eight cylinders). Load the closest
  vendor base map instead of starting from a reset (`practice` RB25 part 1).
### Inputs, outputs and calibration
- MAP calibration against the onboard baro fails when the wrong MAP sensor is selected, so it doubles as a check. With
  the key on and the engine off, MAP should equal baro and MGP should read zero.
- TPS calibration is easy to skip, and one car read 99.1 % at full throttle. Sweep the throttle slowly after
  calibrating to find worn tracks.
- Digital inputs: a switch to ground uses pull-up on, active low and the falling edge, while a switch to 12 V uses
  pull-up off and active high. A 350Z clutch switch goes to 12 V. Confirm the state in runtime values. A clutch switch
  at the bottom of travel activates only after the clutch has released, so in one case the engine flared from 5500 to
  about 6175 rpm before the cut.
- On piggyback installs where the factory ECU already biases a temperature sensor, turn off the G4+ pull-up.
- The VTEC output sits on a different aux output for each plug-in variant (about aux 5 on OBD1, aux 6 on OBD2).
- On some early firmware and some digital inputs, the flex sensor fuel temperature read nonsense while ethanol content
  read correctly (the edge or the input did not support the decode).
- An analog wideband input is skewed by small ground offsets, and the predefined wideband calibrations cannot be
  edited. Use CAN, or a two-point user calibration checked against a trusted reference at two lambdas (an offset of
  about 0.04 lambda was typical in one session).
- The fan output needs the rpm-zero timeout, or it runs the battery flat while the ECU is powered with the engine off.
  Shift lights and similar outputs flicker unless they have a short switch-off timer.
- `vendor-doc`: aux back-feed: a relay or solenoid powered from permanent battery or ACC on a flywheeled aux output
  sends current back through the diode and half-powers the ECU. The signs are an ECU that stays on after key-off, fans
  that run with the key out, chattering relays and a battery that goes flat after a few days. Power aux loads through
  the main relay, which is ignition switched; note that many Nissan ISC solenoids are fed hot. For the same reason the
  e-throttle relay (VQ35 example) should sit on an ignition or injection channel without a flywheel diode.
- `vendor-doc`: the fan rpm-zero timeout runs only while hold power keeps the ECU alive. Without hold power the fan
  stops at key-off regardless of the timer. Above the non-driven speed lockout the fans stay off even when hot (5 km/h
  hysteresis; 0 disables it), so a low lockout can overheat the engine at moderate speed. Fans also do not run if the
  engine has not run since power-up.
- `vendor-doc`: Test On for an aux output also triggers whatever is keyed to it (dual fuel tables, for example).
  Before the first start on a plug-in, exercise each output with Test On or Test PWM (10 Hz) and check each input in
  runtime values, because one plug-in serves several variants. On some Evo IV to VIII the fuel pump and A/C clutch
  outputs are swapped relative to the base map; if the pump does not prime, swap them.
- `vendor-doc`: spurious analog faults: some MAP sensors reach 0 V in deep vacuum (and fault on overrun), and
  narrowbands reach 0 V when lean. Set Error Low to 0.00 V on those channels. Thunder's An Volt 13-16 read anything
  below 0.1 V as 0.0 V, so keep narrowband and other low-voltage signals off those inputs.
- `vendor-doc`: the help gives edge detection for DI 1-8 in one topic and for DI 1-6 in its GP input topic. Check in
  the software before using DI 7 or 8 for gear cut edges (see `quirks-ignition.md`, Disputed).
- `vendor-doc`: random over-speed spikes on a wheel speed input usually come from an odd signal shape. Try the
  opposite trigger edge.
- `vendor-doc`: the help numbers aux states on a table axis inconsistently. Read the state's runtime value before
  setting breakpoints.
- `vendor-doc`: assigning one function (IAT, for example) to two channels mismatches calibration and sensor and spoils
  the charge temperature corrections. Two thermistors in parallel also spoil the reading, for example an old AFM IAT
  that is still connected while its wiring is reused.
- `vendor-doc`: factory MAP sensors on plug-ins top out below many boost targets. WRX V1 to V6, RB25DET and early MR2
  sensors stop at about 125 kPa (18 psi) boost, the Subaru V10 sensor at about 160 kPa absolute, and RX-7 S6 to S8 at
  220 kPa absolute (about 1.2 bar boost at sea level). The recommended internal sensors are 1.5 bar boost on VLLink
  and 3.0 bar on Nissan plug-ins and several others. On such a car a flat-topped MAP trace shows the sensor's range,
  not the boost. The RB25DET factory plumbing also misses part of the vacuum-to-boost range.
### ECU setup traps
- `vendor-doc`: out of the box a G4+ is locked. It connects and accepts configuration but will not run an engine until
  its unlock code is entered and power is cycled; optional features are unlocked the same way. On a no-start, check
  the ECU information screen before chasing trigger or fuel faults.
- `vendor-doc`: a forgotten password can be cleared only by Restore to Factory, which wipes the tune and may change
  output states while connected, so make the loads safe first. A map with a password can still be saved and loaded
  elsewhere unless it was also saved encrypted.
- `vendor-doc`: Undo short-term changes returns the tune to its last Store, as a power cycle would, but it has no
  effect once the changed-cell markers have been reset; after that only a power cycle restores the stored tune.
  Nothing undoes a Store except a saved file.
- `vendor-doc`: from 5.6.0, codes can be cleared without a laptop: with the key on and the engine off, hold the
  throttle above 80 % for 10 s. Starting the engine or lifting off aborts the clear. Until they are cleared, stored
  codes reappear in the PC event log. Once rpm is above zero the CEL stays lit steadily and flashes no codes.
- `vendor-doc`: an analog input must be outside its limits for 1 s before it faults; e-throttle sensors take 2 s.
- `vendor-doc`: for a first start, use Master Fuel to get the engine running (more Master Fuel means richer). Once it
  is warm, redo the base timing and store.
### Firmware-version traps
- `vendor-doc`: (release notes) the calculation for a Modelled tune using BAP as the equation load source was
  corrected in 5.6.3, so a tune made earlier fuels differently after the update and needs a retune. Before 5.2.0,
  tunes running 1/2-cycle group injection received twice the fuel in that mode; retune them once updated.
- `vendor-doc`: when moving to 5.1.0 or later, zero the new short pulse adder tables unless the injectors are
  characterised (5.3.0 brought negative adders and a fresh setup). Turn charge temperature correction off or set it
  up, or the tune moves. Sec PW Lockout switched from actual to effective pulse width (after 5.0.3), so subtract the
  secondary dead time at normal voltage from the previous figure (2.000 - 0.660 = 1.340 ms).
- `vendor-doc`: since 5.5.1 the AC, fan and drive idle pulse-width adders are held at zero in Modelled modes, and the
  TP and AP fault thresholds are in volts instead of percent. Recheck both on a tune brought across.
- `vendor-doc`: since 5.6.5, losing a CAN-lambda signal zeroes that lambda, and zeros are excluded from the average.
- `vendor-doc`: G4+ units with support processor firmware revision 0 (not Atom) may give a prime pulse that differs
  from the table. Measure the injector open time during prime, and if it differs, ask the vendor about an upgrade.
  Before firmware V1.60, wakeup had a single width and known faults.
- `vendor-doc`: some channels misreport on older firmware: MAF measured g/cyl before 5.2.0, AFR average before 5.6.6,
  signed CAN integers before 5.6.7, closed-loop lambda 3D trim limits until the 5.6.8 fix, and CAN1 failed with CAN2
  enabled before 5.1.0. Do not derive corrections from those channels in older logs.
- `vendor-doc`: other defects by version: knock retard and per-cylinder ignition trims were unreliable on 5.6.0 to
  5.6.3 (critical fix in 5.6.4); 4D/5D ignition tables holding 14 or more could command -100 deg on 5.5.1 to 5.5.4;
  post-start hold and decay were wrong on the first start after power-up before 5.3.1; and multi-fuel post-start
  finished on warm-up table 1 rather than the blend before 5.2.2. From 5.6.1, VVT control begins at engine start
  instead of waiting for the speed lockout.
- `vendor-doc`: idle history: the fan idle step was broken from 5.0.4 until 5.4.3; fan idle trim has been forced to 0
  above 2000 rpm since 5.6.2; and idle target as an axis and the idle gain tables were fixed in 5.6.7. In 5.5.3 the
  hold (dashpot) step became adjustable (previously fixed at 2 % duty or 10 steps), a speed lockout setting appeared
  (previously effectively 2 km/h), and 3D tables for base position, target trim and N/P step arrived. After an update,
  check or zero them.
- `vendor-doc`: updating keeps the tune, but new features left misconfigured can hurt the engine, so read the notes of
  every release after the installed one, not just the newest. Update with CAN and serial devices disconnected, the
  ignition on, the engine off and the battery stable. Afterwards power down for about 5 s (pull the battery if the
  prompt persists). A Safe Mode message after the update is expected: store, and it clears at the next power cycle.
  PCLink holds a backup tied to the old firmware until the update completes.
### Software, logging and CAN
- Live edits are lost at power-down unless stored, and undo only goes back to the last store. Store often, and use
  save-as to keep the original. Edited cells show blue until they are stored or cleared.
- On wire-in units, a display sharing the serial link stops PCLink from connecting; unplug it. In one session an
  intermittent USB cable dropped the connection repeatedly, so confirm the ECU is online after each store.
- Custom layouts are lost on a PCLink update unless they are saved by name.
- PC logs open with about 100 samples of history captured before record was pressed, marked by a dotted line; onboard
  logs have none. Only the latest PC log shows in the main view, and earlier runs are in the log file manager. The
  record hotkey controls PC logging only, not onboard logging.
- Onboard logging must be configured and verified before the car leaves. Default rates are near 25 Hz, with slow
  channels (coolant) near 2 Hz, and logging is triggered by rpm or a switch.
- CAN streams (ViPEC and G4+): two channels that both default to start bit 0 overlap, and the layout turns red. A user
  transmit channel number must match its stream number. Widths are in bits, though some receivers use bytes. IDs show
  in decimal while other tools show hex (1000 decimal is 3E8). A receiver applies its own scaling, so a factor-of-ten
  error usually means a resolution mismatch. Temperatures are often sent with an offset (plus 50 C on a 350Z).
- `vendor-doc`: a firmware update generally leaves the tune alone, but the help advises saving a copy first and having
  the tune re-checked on a dyno after any update. Training adds two points: read the release notes, and never update
  on race day.
- `vendor-doc`: the internal wideband can stay off until the exhaust is hot, which is the normal mode. The help says
  to change that only while tuning cold start.
- `vendor-doc`: a serial dash prevents PCLink connection and firmware updates, while a CAN dash may stay connected
  when nothing uses the serial pins. Through a USB-serial converter the serial fallback runs at 115200 baud.
  Continuous serial streaming stops as soon as any device (PCLink included) communicates with the ECU and restarts
  only at the next power-up; changing the baud rate or stream mode also needs a power cycle. Cycle power after tuning
  so that a serial dash receives data again.
- `vendor-doc`: CAN wiring: 120 ohm terminators at both ends of the trunk, a trunk shorter than 15 m, stubs shorter
  than 200 mm, and a pair twisted 33-50 turns per metre. G4+ ECUs and DisplayLink are internally terminated and belong
  at the bus ends unless their terminators are removed. Each ID must have only one sender; the dash stream at base ID
  1000 also occupies 1001-1003.
- `vendor-doc`: two help examples scale wrongly. Slip is given 0.1 % resolution and a -100 offset, yet its worked
  example (33 % sent as 330) leaves the offset out. The rpm-to-dash example uses multiplier 4, where a dash counting in
  4 rpm steps needs rpm / 4 (`derived` from that example's own table). Test either one against a known value first.
- `vendor-doc`: install PCLink (it includes the USB driver) before connecting the ECU, and use the PCLink build that
  matches the firmware. Otherwise Windows may attach a wrong driver that is hard to remove.
- `vendor-doc`: dyno channels come in through PCLink on the laptop's serial link, not through the ECU, and are recorded
  only if they are added to the PC logging list.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
