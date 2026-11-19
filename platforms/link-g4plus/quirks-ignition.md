---
id: platforms/link-g4plus/quirks-ignition
title: Link G4+ quirks: ignition, triggers, knock and cams
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-17
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/link-g4plus/quirks]
supersedes: []
---
# Link G4+ quirks: ignition, triggers, knock and cams

Part of `quirks.md`, which holds the overview, scope and sources; read it first. This file holds the ignition, triggers, knock and cams gotchas and workarounds.

## Practical use

### Knock readings
- Knock gain at 2 doubles the raw signal; on an Evo 8 with a flat-response sensor it gave readings near 1000 that
  meant nothing. Set gain 1 and recheck (`practice` Evo 8 part 4).
- A threshold of 1000 (the maximum) disables detection while keeping logging; use it to record the noise floor.
- One practitioner found G4+ knock levels inconsistent from pull to pull on two of three live-training cars, and saw
  retard on one cylinder only after a timing increase (one practitioner's experience). Treat onboard knock as a watch
  item until it proves repeatable on that car, and isolate a suspect cylinder with its own trim. Another practitioner
  trusts a validated setup to about 99 % and uses per-cylinder knock to trim individual cylinders.
- A single marginal count on ethanol at modest timing points to a threshold set too low rather than to real knock. On
  gasoline the same reading deserves more concern.
- If stored per-cylinder retard must persist long enough to inspect, lengthen the advance-back time temporarily.
- `vendor-doc`: KnockBlock G4 reports the knock level as a pulse width on a digital input. That input needs its
  pull-up off, or nothing arrives.
- `vendor-doc`: the status "OFF: DI5 Pullup" means that on some ECUs knock control is blocked while DI 5 has its
  pull-up enabled. "No Signal - DI Feedback" means an external digital knock device was expected but sent nothing.
- `vendor-doc`: a large spectrum spike that is present whether or not there is knock is electrical pickup. Check the
  shield, ground and termination of the knock sensor.
- `vendor-doc`: with Clear I-Trim Tables off, start-up timing is retarded by the stored trims and knock control
  brings it back up. This is safe only if those tables were correct when they were stored.
### Ignition hardware
- `vendor-doc`: most igniters want Spark Edge Falling (dwell begins when the output goes high, spark on the falling
  edge); some Honda, Ford and MSD units want Rising. Prior to 4.3.7 the field was named Dwell Edge and its options
  were reversed, so old notes saying Rising for an ordinary igniter mean Falling now. The wrong edge keeps coils
  dwelling almost constantly, so set it before the coils are connected.
- `vendor-doc`: Honda factory igniters have reversed polarity compared with most. Leave the distributor unplugged
  until the edge is set and stored, otherwise the coil and igniter may be damaged. Ford TFI needs Rising with the TFI
  module left on the distributor, and Falling with any other igniter.
- `vendor-doc`: not every igniter limits current, and some coils (GM/Holden LS1) fire on their own when dwell passes a
  built-in maximum. On those coils, excess dwell acts like extra advance and can cause serious engine damage.
- `vendor-doc`: BMWLink, MiniLink and Arctic Cat 1100T have internal igniters on Ign 1 and 2 only, rated 10 A per
  channel, so keep coil current below that. MiniLink outputs 3 and 4 lack igniters, and wiring a coil straight to them
  damages the ECU. Moving BMWLink to an external igniter needs pull-ups of about 470 ohm from +5 V on all outputs, plus
  Spark Edge Rising, which then applies to every output.
- `vendor-doc`: Skyline plug-ins fire six cylinders in wasted spark from four drivers, with channels 3 and 4 joined.
  Ignition drive 4 must stay unselected, or it fights channel 3. S13Link carries a CA18DET/SR20DET jumper (S13 = CA18,
  S14 = SR20); if it is set wrong, cylinders 3 and 4 get no spark or the wrong one. S13/S15Link need the ignition mode
  (distributed or direct) matched to the engine before running.
- `vendor-doc`: igniters must not sit on or close to the ECU. Place them near the coils, clear of exhaust, turbo and
  radiator heat, on soft mounts, with high-current wiring in a separate loom. One igniter channel must never serve two
  coils: spark energy falls and running turns erratic.
- `vendor-doc`: ignition noise control has four parts. Use resistive HT leads (typically 1000-5000 ohm depending on
  length; avoid spiral and solid core). Use resistor plugs with a few thousand ohms from terminal to centre (some race
  "resistive" plugs fall short). Fit a 0.5-3 uF suppressor between coil positive and ground (one per bank on V and
  boxer engines). Route igniter inputs apart from the igniter outputs and the ECU loom.
- `vendor-doc`: PCLink dropouts or laptop freezes, mostly at full power on the dyno, nearly always mean ignition or
  solenoid noise is corrupting USB. That is an install fault that can also disturb the engine electronics. Inspect
  the plugs and leads, the ECU and engine earths (failures seen include an ECU earthed via a removable loom connector
  or to a rubber-mounted manifold), the igniter earths, coil supply suppression and lead lengths, and bond the car to
  an earthed roller dyno. Dropouts with the engine stopped point at the PC (USB driver, selective suspend, FIFO).
- `vendor-doc`: high-load misfire on a boosted engine usually means spark energy is too low for the cylinder
  pressure. A smaller plug gap, down to about 0.5 mm if needed, cuts firing voltage and radiated noise.
### Cam control
- `vendor-doc`: a relay cannot follow PWM, so cam solenoids never go through one. OEM solenoids switched on the 12 V
  side need rewiring so that Aux 1-4 switch their ground. If this is wrong, cam timing becomes unpredictable, which
  can damage the engine.
- `vendor-doc`: wire cam inputs like triggers (sensor ground, shielded cable); without shielding, cam position errors
  follow. A count of 1 or 2 on the cam error counter at start-up is fine. A count that rises while running points to
  the wrong edge, pull-up or pattern, or to a poor signal.
- `vendor-doc`: on a cam signal error, control of that cam stops and the cam parks. Cam Signal Status names the
  fault. A numbered pulse out of place means the pattern does not match the mode, or the cam is outside its window.
  Missing or extra pulses mean the edge, noise or pattern is wrong. No signal means a wiring or sensor fault. VVT that
  seems dead on a cold engine is often just the ECT lockout.
- `vendor-doc`: an error-free status after the offsets are set means position is read correctly, so a cam that still
  misses its target is down to the solenoid, wiring or PID. VVT stops completely with reversed sensor wiring or wrong
  arming voltages.
- `vendor-doc`: VANOS on BMW S52 and S54 uses 50 Hz, unlike the 250-300 Hz of most VVT (S65: 250 Hz). Diodes inside
  the S50 connectors and the S54 VANOS module stop ground-side PWM. Remove them, and on S54 move pins 2 and 5 onto
  key-on 12 V.
### Triggers
- The trigger 1 error counter rises when too many or too few trigger 1 teeth are seen between trigger 2 events. One to
  three at start-up sync is normal; any rise while running is not. A drift ute that was down about 125 kW with jagged
  power had 222 errors. Its cam sync edge had moved next to a crank tooth, and the fix was triggering on the other
  edge, not changing the offset (`practice` session 095).
- The statistics window shows maxima since reset and does not refresh live; an impossible maximum rpm flags trigger
  errors.
- The built-in trigger scope captures 720 deg, is not lab grade, and is meant for cranking and idle.
- Timing readings while cranking wander because few teeth are seen, so confirm the offset at a steady idle. After
  cranking tests with injection off, remember to re-enable it.
- `vendor-doc`: missing-tooth wheels with a poorly designed gap cause trigger errors. This mainly affects high tooth
  counts such as 60-2 with reluctor sensors, and it gets worse at high rpm.
- `vendor-doc`: changing Trigger Mode loads that mode's presets into every trigger parameter, including the offset, so
  base timing shifts. Recheck all trigger settings and the timing mark afterwards.
- `vendor-doc`: the Trigger 1 error counter checks the tooth count across 720 deg. In cam-sync setups Trigger 2 sets
  that window, so one extra or missing Trigger 2 pulse raises the Trigger 1 count even with a clean crank signal; look
  at both. Other listed causes are an incorrect tooth count or sync mode, a moving wheel or sensor (vibration, belt
  stretch), wiring, interference, a badly designed wheel, incorrect arming voltages, and a sensor saturating at high
  speed with many teeth. Treat erratic engine speed as a trigger fault until proven otherwise.
- `vendor-doc`: the help's example of a badly designed gap, on a reluctor 60-2 wheel (some OEM ones such as BMW
  included), lost the tooth after the gap near 7500 rpm. The next tooth became the reference and all cylinders gained
  about 6 deg of advance. Sudden timing jumps or lost sync only at high rpm on such a wheel suggest a gap-design
  problem, which Hall sensors seldom show.
- `vendor-doc`: in 1 tooth per TDC mode the offset cannot be moved in software with timing locked, so base timing is
  set by turning the sensor or distributor. With few teeth, position updates slowly while cranking and dwell is shorter
  than the table asks. Raise the low-rpm, low-voltage dwell cells to 2-3 times the running dwell.
- `vendor-doc`: do the trigger calibration with injection disabled and stored, so the engine cannot start. Then check
  the mark again while it runs steadily at 2000-4000 rpm, because crank speed fluctuates within each revolution during
  cranking (see `semantics-ignition.md`, Disputed, on the speed).
- `vendor-doc`: the trigger scope records 720 deg or more, so its time base follows the rpm the ECU sees. Reluctor
  inputs are shown AC coupled, and optical and Hall inputs DC coupled. A wrong trigger type, position, pull-up or rpm
  reading invalidates a capture, and the AC view hides a DC offset caused by a reluctor wiring fault. Precise work
  needs a genuine electronics oscilloscope, because many automotive scopes sample too slowly.
- `vendor-doc`: ground a spare Trigger 2 input, or configure it as Hall with pull-up, so it cannot float and collect
  noise. Disable trigger pull-ups on a piggyback install where the factory ECU supplies its own. Trigger cable shields
  are not grounded at the sensor end, and no sensor shield goes to the block.
- `vendor-doc`: the GT101 Hall sensor reacts to supply noise and is unsuitable for crank triggering; use it for
  low-tooth, low-speed speed inputs. +8V Out serves only optical or Hall crank sensors, and plug-ins built on Atom and
  Monsoon do not have it.
- `vendor-doc`: the help calls trigger faults the most common install problem; they can destroy an engine instantly
  or stay hidden until a critical moment. Do not make the first start until both trigger configurations are certain.
  Do the initial tuning with antilag, launch and gear cut off and only one boost table active.
### OEM trigger and cam pages
- `vendor-doc`: engine-specific help pages are only a general guide, so verify each listed offset with a timing
  light. On Nissan CAS engines (SR, CA, RB, VG, VH, FJ) the sensor can be rotated, so no offset is fixed. The quoted
  widest-slot values are about 24 deg for RB20 and RB25, 9 deg for RB30 and 16 deg for SR20.
- `vendor-doc`: some pages have known errors. The Mitsubishi GTO and Buick 3.8 pages show 4 cylinders with V6 firing
  orders. The Holden Ecotec II page carries a copy of the Ecotec III quad-cam VVT block. The threshold table for the
  Honda 15x jet ski has 0 at 1000 rpm. Correct these before use.
- `vendor-doc`: variants of one engine with and without VVT can need very different offsets (1JZ-GTE about 200
  against 355; 1UZ-FE 234 against about -4). Near-identical variants can need different modes (MX-5 pre-OBD2 against
  OBD2; Evo I-VI Trigger 2 on the falling edge, Evo VII-IX on the rising edge). A base map for the wrong variant gives
  wrong sync or timing.
- `vendor-doc`: the correct mode can carry another maker's name (VR6 runs the Holden V6 Ecotec III VVT trigger mode;
  Chevrolet LT1 Optispark runs Nissan 360 optical). Dealers found that some 2ZZ-GE engines would only sync in 2NZ-FE
  mode. A Renault Clio that will not run in any built-in Renault mode is cured by a 60-2 wheel conversion.
- `vendor-doc`: the 2GR-FE cam sensor output is weak and often needs an external pull-up to 5 V (about 1 kohm on a
  trigger input, 2.2 kohm on a digital input) with the internal pull-up off.
- `vendor-doc`: on WRXLink V3-4, rough running with unsteady rpm and a rising trigger error count usually means the
  crank and cam polarity DIP switches are on the wrong option. Some cars (notably those with a factory immobiliser)
  have reversed CAS wiring, and nothing visible shows which. Try the other setting.
### Rotary
- `practice` (session 043): on the G4+, trailing split values are negative for trailing after leading. A positive
  value makes the trailing plug fire before the leading plug, which is dangerous. This catches tuners used to ECUs
  that take the split as a positive delay. Confirm the sign in the software before entering a split.
- The rotary-only limiter mode cuts fuel and spark together, and it is made gentle because popping can damage stock
  apex seals.
- `vendor-doc`: metering oil pump feedback voltages differ slightly between two help topics (about 0.8 or 0.9 V
  closed, 4 or 4.4 V open). Calibrate on the car rather than copying either.

## Disputed / conflicts

- **Onboard knock reliability.** One practitioner found it inconsistent on several cars (opinion); another trusts a
  validated setup and tunes individual cylinders from it. Both back it up with audio detection when tuning.
- **Idle ignition throttle lockout.** Training found that 1.5-2 % kept retarding on a gentle pull-away, and sets it
  about 0.2 % above the logged closed reading. The help's idle ignition topic suggests 1.5 % TP/AP. To test, log the
  lockout state against TP on a slow pull-away.
- **Edge-triggered digital inputs.** The help's digital inputs overview lists DI 1-8, while its general purpose
  digital input topic lists DI 1-6.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
