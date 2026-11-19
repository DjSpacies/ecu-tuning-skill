---
id: platforms/link-g4plus/quirks-control
title: Link G4+ quirks: limits, boost, idle, throttle and launch
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-17
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/link-g4plus/quirks]
supersedes: []
---
# Link G4+ quirks: limits, boost, idle, throttle and launch

Part of `quirks.md`, which holds the overview, scope and sources; read it first. This file holds the limits, boost, idle, throttle and launch gotchas and workarounds.

## Practical use

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
  faulted sensor's real value is unknown (`practice` session 036). The help agrees in effect: 0.00 or 5.00 V
  switches that side of the check off, and it gives 0.05 and 4.95 V as typical (`vendor-doc`).
- `vendor-doc`: the help's typical End Cut of 90 % is paired with a hard limit 200 rpm past the end of the range, so it
  relies on that hard cut. This fits the training finding above that an End Cut below 100 % without a hard cut may not
  hold rpm.
- `vendor-doc`: a latched launch with the default 200 rpm limit range keeps cutting until rpm is 200 below the set
  point. Use advanced limiting with a range of 0, and never use Always On activation.
### Overrun, kill and other cut sources
- `vendor-doc`: with fuel-cut limiting, only aux channels set up as primary or secondary injection are cut. Aux
  injectors used for extra fuel, nitrous or water keep firing, so choose ignition cut whenever auxiliary injection
  runs.
- `vendor-doc`: if enabled, fault codes 1 and 2 record RPM and MAP limit activations. Seen in normal running, they do
  not mean a hardware fault.
- `vendor-doc`: several functions can kill the engine with a full fuel and ignition cut: anti-theft, the stop switch,
  the throttle safety switch, ECU hold power, the over-voltage limit, starter control (start/stop or touch-start), and
  dual ECU mode, which also disables the trigger inputs. If the engine cranks and the trigger is fine but there is no
  fuel or spark, read Engine Kill and Anti-Theft status before anything else.
- `vendor-doc`: in Start/Stop starter mode, pressing the button above the deactivation rpm imposes a full fuel and
  ignition cut until the engine stops, so a total cut in a log can simply be the start button. Since 5.5.6 a second
  Touch Start press also stops the engine. Starter Test mode bypasses all checks.
- `vendor-doc`: the analog throttle safety switch (powersport) reads about 1 to 2 V with the lever released and 2.5 to
  3.5 V when pressed. Released, the engine runs only with TP 0 to 3 % and is killed at 4 % or more. Any other voltage
  is a circuit fault and kills the engine.
- `vendor-doc`: a closed-loop stepper (throttle stop, wing or rotary oil pump) that cannot reach its target in time
  flags a fault and holds the engine to 2000 rpm.
- `vendor-doc`: torque management uses only the peak of its torque estimate table, and reads it once at power-up.
  After editing the peak, store and power-cycle.
- `vendor-doc`: in cyclic idle, a fixed 100 % fuel cut applies if rpm goes more than 500 rpm over the cyclic limit.
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
- `vendor-doc`: gear, ECT and IAT wastegate trims carry the same names in both modes but act differently. Open loop:
  they scale base duty (50 % with a 10 % trim becomes 55 %). Closed loop: they add duty points (50 % with 10 % becomes
  60 %). Copying a trim from one mode to the other changes its effect.
- `vendor-doc`: the ECT and IAT wastegate trims alter duty only; boost target has its own trim tables.
- `vendor-doc`: the stage hysteresis example in the help contradicts its own definitions, and the P-term example
  formula has a sign error; check stage changes and P action in a log instead of trusting the text.
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
- `vendor-doc`: Drive Trim adds fuel whenever the neutral/park input is off, so with no N/P input assigned it applies
  all the time, because a missing N/P signal reads as in drive. Leave it at 0 unless the input exists.
- `vendor-doc`: the closed-throttle switch input is for display only on this firmware; idle control ignores it.
- `vendor-doc`: with no non-driven wheel speed source configured, the idle ignition speed lockout never trips, so the
  idle table stays in charge until another lockout does.
- `vendor-doc`: steppers work the opposite way to solenoids: extra steps lower idle. A stepper whose idle rises with
  base value is wired in reverse; change the direction setting or swap Aux 5/6 (seen on some VR4Link installs).
- `vendor-doc`: stepper outputs are Aux 5 to 8 only, and windings below about 20 ohm may overheat. Two-terminal
  solenoids use Aux 1 to 8, or an ignition channel with a flywheel diode, never an injector channel, and need switched
  power (some Nissan valves come battery fed). Three-terminal solenoids use Aux 1 for close (slave) and Aux 2 for
  open, with each coil over about 10 ohm.
- `vendor-doc`: the Key ON stepper reset runs the valve fully open and back, taking up to about 4 s; cranking during
  it can flare to about 4000 rpm (WRX/STI example). A Key OFF reset using an ignition-switch DI plus ECU Hold Power, or
  Key-On Fuel Lockout, is better. Over-driving at reset can make a stepper lose position; begin with low base values
  (for example 50) and cycle the key a few times.
- `vendor-doc`: the help describes the same rolling-stop stall as above: closed loop shuts the valve while rolling,
  then must open it a long way and undershoots. Its speed lockout figure differs between topics (see
  `semantics-control.md`, Disputed).
- `vendor-doc`: heated bimetal fast-idle valves add air that the ECU neither controls nor sees.
### Electronic throttle faults
- `vendor-doc`: feedback is minimal in ON-Setup, so the plate following the pedal there proves little. ON mode
  cross-checks main against sub for both TPS and APS, and any unexpected relation stops ETC. A sub track that flattens
  near the top, or moves slower than the main, is normal; erratic behaviour is usually wiring. Plot both voltage pairs
  across full travel.
- `vendor-doc`: Category 1 and 2 faults (motor, TPS integrity) open the e-throttle relay at once and enforce a fixed
  rev limit through cyclic fuel cut (figure in Disputed), held until a power cycle. ETC codes persist in storage;
  clear them in PCLink after every repair.
- `vendor-doc`: thresholds, each needing 2 s to set: motor duty within 5 % of its maximum or minimum (stuck plate,
  disconnected motor); driver supply below 7.0 V; sensor 5 V below 4.85 V (weak battery during cranking or a sagging
  rail can trigger these); plate more than 2 % off target when steady (more allowed while target moves); TP main/sub
  disagreement; a track at ground or at 5 V. The TP/target error accumulator bleeds off, so short transients are
  tolerated and only lasting mistracking sets a fault.
- `vendor-doc`: Category 3 (pedal) faults give limp-home rather than shutdown: AP(Main) is held at 5.0 %, throttle
  control continues, and the target table's 5 % pedal value applies (aim for about 2000 to 4000 rpm). Main and sub
  more than 3.0 % apart for 2 s sets code 77; check AP sub 100 first. ETC shuts down when the AP error accumulator
  reaches 255, so occasional pedal glitches add up. In CAN mode, AP(Main) not refreshed for 1 s is a fault.
- `vendor-doc`: Toyota and Lexus pedals with a saturating sub track cause AP tracking faults and an ETC shutdown if the
  non-linear point is left uninitialised; linear pedals take 100 %.
- `vendor-doc`: automated TPS calibration runs with e-throttle 1 in ON-Setup and the engine off, and takes about 15 s.
  If duty reaches 80 % and the TPS does not move, the TPS or motor is unconnected or the fault levels are wrong. If
  duty reaches 80 % but the movement is not as expected, the motor polarity is reversed or the plate is blocked.
  Travel under 1.5 V means wrong polarity. A 3 s timeout with no stable end point points to noise pickup, bad grounds,
  an unstable 5 V supply, or a plate unable to reach its stop. The routine has its own error codes, and running it
  wipes stored ETC codes.
- `vendor-doc`: keep the e-throttle driver supply off until the ECU is configured, or the plate may be slammed open or
  shut. First setup sequence: remove the relay, configure outputs, calibrate the APS, select ON-Setup, fill the target
  table, refit the relay while watching for the plate snapping open, calibrate the TPS, tune the loop, select ON, then
  clear codes and confirm they stay clear. The relay must use a physical output, not a virtual aux.
- `vendor-doc`: the Ford BA Falcon body's TP sub reaches only 67 % at full open, and the Toyota clutched body (3S-GTE,
  1UZ-FE) 68.5 %; enter that figure as "TP sub 100" or main/sub tracking faults result. The Toyota throttle clutch is
  driven as Test PWM at 250 Hz on a native aux channel. The RX8 plate can travel past 90 deg, so take care where the
  open end point is calibrated.
### Launch, anti-lag, shift and traction
- `vendor-doc`: in Degrees mode the anti-lag and launch ignition trims are added to the present timing, so a negative
  number retards by that much rather than naming a final angle.
- `vendor-doc`: per-gear shift tables (cut, retard, fuel, durations, blip) are looked up by the gear being left, not
  the one selected. For example, Max Down Shift RPM 5000 in 3rd refuses a downshift out of 3rd until rpm drops under
  5000 (status RPM High Lockout). With no gear detection the gear 0 cell is used throughout; the older gear cut (5.2.2
  and earlier) uses gear 1's cut time for gear 0.
- `vendor-doc`: the ON state of Gear Cut Status is stretched beyond the true cut so that it stays visible; do not
  measure cut time from it. Force GDI units report shift cut as fuel cut %.
- `vendor-doc`: with the traction non-driven speed lockout set too low, traction control can intervene during launches
  or tight pit turns. For a momentary disable, press for over 1 s and release to turn it off, and press for over 0.2 s
  to turn it back on.

## Disputed / conflicts

- **Closed-loop boost on G4+.** Two training sessions report road overshoot they could not tune out and use passive
  MAP-axis open loop instead; the help and other training sessions set up and use the staged closed loop routinely.
  The disagreement may be firmware-dependent. Test: compare boost error on road or track logs, not the dyno, for both
  methods on the same car.
- **MAP limit control range default.** A course lesson gives 10 kPa, a turbo session 20 kPa; the help's MAP limit
  topic calls 10 kPa typical. Read the setting in the tune rather than assuming.
- **E-throttle fault rev limit.** The help's limit status topic gives 1800 rpm, and its safety features topic gives a
  fixed 1800-2000 rpm. Neither is adjustable.
- **Closed-loop trim limit shape.** Training describes one symmetric limit, but the 5.6.8 release notes fix 3D
  closed-loop trim limits, which implies a table in some builds. Read the field in the tune's firmware (see
  `semantics-control.md`, Disputed, for values).

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
