---
id: platforms/link-g4plus/semantics-control
title: How Link G4+ tables behave: limits, boost, idle, throttle and launch
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-17
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/link-g4plus/semantics]
supersedes: []
---
# How Link G4+ tables behave: limits, boost, idle, throttle and launch

Part of `semantics.md`, which holds the overview, scope and sources; read it first. This file holds the limits, boost, idle, throttle and launch settings and how they behave.

## Why (derivation)

### Limits
- `vendor-doc`, `practice`, `practice`: rpm and MAP limits have a control range below the table value (defaults
  in the sources: 200 rpm, and 10 kPa in one course lesson, 20 kPa in one turbo session). Cutting starts at
  (value - range) and reaches End Cut at the value. In advanced mode the entry cut is interpolated between Start Cut at
  low throttle and Start Cut at 100 % throttle, because more power needs more cut, and an optional hard cut acts a set
  margin above the value. Cut sequencing is adaptive by default, so the start values are only a starting point.
- When several rev limits are active the ECU applies the lowest.
### Closed-loop controllers
- Lambda: in Auto mode the trim follows the target table with an error-indexed gain table and an rpm-indexed update
  rate; in the stoichiometric modes it dithers around lambda 1 for the catalyst, with one gain (`practice`
  session 086). The update rate must stay slower than the transport delay from injector to sensor, which is long at
  idle because exhaust mass flow is low; updating faster than that delay makes the loop correct twice for one error
  and oscillate.
- Boost: stage 1 holds a fixed spool duty, stage 2 adds base duty plus P and D near target, stage 3 adds P and I for
  residual error, with hysteresis between stages. The base duty table is a feed-forward prediction of the duty needed
  for each target (`practice` tutorial 10.16, `practice` RB25 part 5).
- Idle: the idle ignition table is indexed by rpm error from the idle target table; positive error means rpm below
  target and should add timing. Spark changes torque within a cycle while air control lags, so timing does the fast
  correction and air the slow one (`practice` tutorial 10.13, `practice` idle ignition session).

## Practical use

### Limits and protection
- RPM, MAP, speed and launch limits can be ignition, fuel or combined cuts. With group injection or auxiliary
  injectors the help recommends ignition cut. A correct boost setup should never reach the MAP Limit, and the limit
  does not directly control pressure. Rpm can still be exceeded on down-shifts. Rotary mode cuts fuel and spark
  together for the gentlest limit, because popping can harm apex seals.
- Control range width: about 200 rpm gave smooth control; 20 rpm behaved like on-off and overshot about 130 to
  150 rpm; 500 rpm was smoothest but settled 100 to 150 rpm low at full throttle. Fewer cylinders means coarser control
  per cut event (`practice` sessions 084, 171). Adaptive (random) cut avoids cutting and fouling one cylinder.
- Rev limit and MAP limit versus coolant are the free protection: lower when stone cold and stepping down above about
  110 C. GP limits index a limit on any input (oil pressure, lambda, clutch, throttle): fill the safe area well above
  the main limit (10000 rpm in the sources) and the protected area with a low limit. Oil pressure protection wants zero
  or very short activation delay plus a start-up lockout of a second or two; lambda protection wants about 2 s of delay
  and only at high throttle, because lifts, shifts and transients give brief lean readings.
- `vendor-doc`: the protection limits are RPM, MAP, GP RPM (3D), vehicle speed and system voltage, and every one uses
  the progressive limiter. The system voltage limit stops the engine above its shutdown voltage, for example after a
  charging failure or a bad jump start.
- `vendor-doc`: the help's typical advanced settings are a control range of 200 rpm (a 7000 limit then acts from 6800
  to 7000), Limit Ignition Trim of -5 deg (retard on the rpm, MAP and speed limits in addition to cutting), a hard
  limit 200 rpm beyond the end of the range, adaptive cut, End Cut 90 %, full-throttle Start Cut (TP 100) 60 %,
  low-throttle Start Cut (TP Low 15 %) 30 %, and an exit decay of 1 % per 20 ms. A low-throttle Start Cut of 0, or one
  above the full-throttle value, is ignored and only the full-throttle value acts.
- `vendor-doc`: in a good limiter log the % cut settles inside the control range. If it does not, soften the gradient
  with a wider range or with Start and End Cut closer together. Overshoot that later settles on full-throttle hits
  calls for a higher full-throttle Start Cut. The Percentage Fuel Cut and Percentage Ignition Cut channels report the
  fraction of events that was cut.
- `vendor-doc`: the MAP limit control range is typically 10 kPa (acting from 190 to 200 kPa for a 200 kPa limit), and
  the hard-limit offset is the same. The X axis is usually ECT, which gives a lower limit when cold and a limp value
  when hot. Dual tables selected by an input are optional.
- `vendor-doc`: the speed limit takes a driven or non-driven source, can be switched for pit lane use, and typically
  runs a 5 km/h range. For a 60 km/h pit limit, enter 55 km/h with a 5 km/h range, then tune how hard it bites.
- `vendor-doc`: the help's oil pressure GP limit uses oil pressure by rpm or TP as axes, a 10 s start-up lockout and a
  3 s activation delay. Its cells hold 500 rpm at 0 psi, 500 to 1500 rpm under 20 psi, 10000 (not limiting) above
  40 psi, and 0 rpm in high-rpm low-pressure cells so the engine is driven down to idle; 0 rpm at 0 psi stalls it. See
  Disputed for the delays.
- `vendor-doc`: in the sustained-boost example a virtual aux that turns on above 120 kPa runs a timer (reset off boost,
  maximum 15 s). The timer serves as a fuel overlay axis that adds nothing for 10 s and then 2 to 10 % by 15 s.
- `vendor-doc`: torque management (in some plug-ins, for TCM or watercraft torque requests) removes torque with
  retard. Its settings are the gain at maximum and at minimum torque (more is needed at high power), the maximum trim
  and the recovery period. Only the shape of the torque estimate table (Nm by load and rpm) matters.
### Overrun fuel cut
- `vendor-doc`: the cut needs throttle below the TP/AP threshold and rpm above the ECT-indexed de-activation rpm. The
  threshold uses APS under e-throttle, a cruise-control mix from 5.1.0, and APS over CAN from 5.6.8. The sequence is
  the activation delay, retard ramped in over the torque reduction time, every injector cut until rpm falls under
  de-activation, and then the retard ramped out. The help's example uses a 5.0 % threshold, 0.5 s delay, 2.0 s ramp,
  -10 deg retard and 1600 rpm de-activation.
- `vendor-doc`: set the TP/AP threshold just above closed to allow for noise (1 % is typical). The activation delay
  can keep the cut out of gear changes. De-activation sits about 500 rpm above idle, which is near 1500 rpm when fully
  warm (80 to 100 C), and higher when cold because the idle target is higher and a cold engine takes the cut badly.
- `vendor-doc`: retard during the cut softens the torque step when fuel returns. The retard moves at no more than
  5 deg/s, so -15 deg takes 3 s even with a 2 s ramp (see Disputed). Under e-throttle, keep the throttle angle very
  small at fuel return to avoid a surge.
### Boost control
- Open loop outputs duty from the base table; closed loop drives duty toward a target table and needs activation
  thresholds and a timeout. The help recommends about 20 Hz for the solenoid in one topic and 15 to 20 Hz in another.
- Activation (training): rpm and MAP thresholds stop the solenoid working while in vacuum; the training sources use
  about 100 to 110 kPa and 1500 to 3000 rpm, the help a lower MAP (see Disputed). A MAP threshold above what the
  spring alone reaches means control never starts; one too close to target leaves no time to manage the rise and
  overshoots.
- Closed-loop setup in the help and course: zero gains and trims, re-axis the base duty table to target by rpm, tune
  base duty until each target is roughly met on the table alone, then add gains softly. Example values from the help:
  P 0.2, I 0.1, D 0.1, 90 % maximum duty, 15 % integral clamp, 90 % stage 1. Stage boundaries in the course: stage 2
  from about 50 kPa below target, stage 3 from about 15 kPa below with about 15 kPa hysteresis and 0.5 s delay. Keep
  base duty referenced in stage 3 if duty changes a lot with rpm, so the integral does not chase it.
- Stage 1 held too long keeps the gate shut and carries the turbo past target: one RB25 overshot from 210 to 236 kPa
  until stage 2 was moved from 50 to 70 kPa below target and base duty dropped from 35 to 30 % (`practice` RB25
  part 5).
- Extras: two target or duty tables switched by a digital input; interpolate-between mode with a pot voltage or the
  ethanol blend as the ratio axis (up to 12 steps from a 12-position pot); gear trim as one static percentage per gear
  that saves a 3D table; IAT and ECT trims as backstops; switching tables via a virtual auxiliary output.
- `vendor-doc`: 0 % solenoid duty gives spring pressure, and 100 % gives whatever the turbo can make, which is normally
  more than is safe. Untrimmed open loop wanders with baro, humidity and temperature, and G4+ closed loop still relies
  on the open-loop base table. Restrictors in the boost lines mean far less duty is needed for a given boost, so each
  duty step moves boost less; the help recommends them especially for open loop.
- `vendor-doc`: the stages start once rpm and MAP both pass activation. Stage 1 holds a high fixed duty (80 to 90 % is
  typical). Stage 2 runs from Stage 2 ON below target (typically 50 kPa, so 150 kPa on a 200 target) and uses base duty
  plus P and D. Stage 3 runs inside Stage 3 ON (typically 15 kPa) after its delay (0.5 s is typical) and uses base duty
  with P and I. D and I are never active at once. Falling more than the hysteresis under the Stage 3 ON point returns
  to stage 2. As MAP or rpm drops, stage 1 re-arms only after the activation lockout is reached, and the deactivation
  timeout keeps stage 2 alive below activation. A small Stage 2 ON stretches stage 1 (faster spool, more overshoot); a
  Stage 3 ON that is never reached means stage 3 never starts.
- `vendor-doc`: gain scaling: P 1.0 with a 1 kPa error gives 0.1 % duty; I 1.0 with a 1 kPa error moves duty 5 % per
  second; D 10 with the error changing by 1 kPa/s gives 0.5 % duty. The integral clamp limits I equally in both
  directions, in % duty. Typical values are P 3.0, D 3.0, I 0.3, an integral clamp of 15 % and a maximum duty of 40 to
  95 %. More P spools faster but overshoots; D damps overshoot, but too much slows spool; I removes a steady offset,
  but too much oscillates. The maximum duty clamp limits overboost while tuning.
- `vendor-doc`: the Boost Control Status values are OFF; rpm or MAP lockout; open loop; stage 1 pre-spool; stage 2 CL
  (P+D); stage 3 CL (P+I); Integral Clamp; and CL-PID Off (every gain 0). Integral Clamp means I is saturated with the
  target still unmet, because base duty is too low or the hardware cannot reach it; fix base duty before the clamp. The
  P, I and D contribution channels show which term drives duty, and a steadily growing I means a lasting error.
- `vendor-doc`: in advanced open loop, with all three gains at zero, only stages 1 and 2 remain and stage 2 outputs the
  base table untouched. Use it to tune base duty one target row at a time.
- `vendor-doc`: the help's setup guide (up to 220 kPa absolute) activates at about 2000 rpm and 80 kPa, with a
  deactivation time of 0 s, Base DC Mode on stage 2, stage 2 from 50 kPa and stage 3 from 15 kPa under target, 10 kPa
  hysteresis, a stage 3 delay of 0.5 s, and an IAT wastegate trim of -12 % at 0 C reaching 0 by 50 C. The target is 2D
  on rpm, and the wastegate table is rpm by target, with rows such as 180/200/220 kPa. Set every target to 180, tune
  that row, repeat for 200 and 220, and only then add gentle PID and refine.
- `vendor-doc`: the help's sample closed-loop sets are only starting points, as gains vary a lot with hardware; each
  uses 80 % stage 1 and Stage 2 ON 50 kPa. EJ25 single scroll: P 1, I 0.4, D 0.4; duty cap 90 %; integral clamp 15 %;
  Stage 3 ON 15 kPa; hysteresis 30 kPa; delay 0.5 s. 2JZ-GTE with GT35R and 50 mm external gate: P 5, I 0.1, D 3; duty
  cap 100 %; integral clamp 20 %; Stage 3 ON 20 kPa; hysteresis 10 kPa; delay 0.2 s. 4G63: P 3, I 0.2, D 3; duty cap
  90 %; integral clamp 15 %; Stage 3 ON 20 kPa; hysteresis 10 kPa; delay 0.2 s.
- `vendor-doc`: in closed loop the wastegate table must have rpm on X and boost target on Y. The gear, ECT and IAT
  target trims add kPa to the target, and the matching wastegate trims adjust duty; move each pair together so the loop
  stays stable. Up to three table pairs can be switched by a DI or aux (the highest number wins), or two can be blended
  through a ratio table (ethanol %, blend or voltage).
### Idle control
- Closed-loop idle needs a speed source, throttle position, and a finished fuel and ignition tune. An ISC solenoid is
  recommended at 200 Hz and must move rpm 300 above and below target at all temperatures (`vendor-doc`).
- Order in the sources: open loop and idle ignition off; set realistic targets; tune the base position per coolant
  breakpoint; then load steps (fan, steering, AC, drive); then the start-up step versus coolant; then closed loop and
  idle ignition. Revisit from a cold start after the main maps. Idle mixture changes idle torque (lambda 1.1 to 1.0
  raised a VQ35 about 40 rpm), so get it right first.
- Lockouts: deadband (25 rpm was called tight), throttle (0.5 to 2 %), speed (about 5 to 10 km/h), rpm above target
  (400 to 500 rpm) and a decel timeout, so the valve is not driven shut on overrun.
- Gains: P about 0.5 to 1.5 worked on every G4+ application in one session; halve if unstable, double if sluggish,
  with big steps so the direction is visible (`practice` session 101).
- Idle ignition: zero-error timing well below MBT (12 deg on a VQ35 whose idle MBT was 24 to 28 deg) leaves room to add
  torque. Offsets in the sources: up to about 15 deg out above target, up to 8 to 15 deg in below. On a 350Z, 10 to
  24 deg moved idle about 200 rpm at fixed throttle, and with the table active a lights-plus-fan load cost about 20 rpm
  instead of about 90. Lockouts above idle MAP, rpm and speed, and a throttle lockout about 0.2 % above the logged
  closed-throttle reading. Idle conditions select the idle spark table; the main table's idle cells still serve the
  transition off idle.
- Drive by wire: the live throttle is base table plus the e-throttle target table, so a hot idle can be set from the
  zero-pedal row of the target table while the base sits near zero.
- `vendor-doc`: closed-loop idle adds its correction to the open-loop Base Position table rather than replacing it. A
  large, lasting CL trim (e-throttle CL idle reports it as % trim) means the base position is wrong; move it until the
  trim sits near zero.
- `vendor-doc`: Base Position is the opening that holds the target with every idle-up off. For a solenoid or
  e-throttle it is % duty, and more is faster. For a stepper it is steps from fully open, so more steps close the valve
  and slow the idle. 2D mode runs on ECT; 3D mode is normally ECT by idle target.
- `vendor-doc`: the idle target is a 2D ECT table, or in 3D mode that table plus a 3D trim (usually run time by
  non-driven speed). With open-loop idle the target never moves the valve; it feeds only idle ignition and the Idle
  Target Error channel.
- `vendor-doc`: the P correction is Idle Target Error x P; too high hunts around the target and too low never arrives.
  D responds to the rate of rpm change to resist sudden loads (excess D overshoots as a load arrives and undershoots as
  it leaves), and it works only in Closed Loop Sol/Stepper. Anti-stall acts like P, but only when rpm is more than
  150 rpm under target. The gains are ECT tables because valve range and engine response change from cold to hot.
- `vendor-doc`: the RPM lockout is added to the target (850 + 400 turns closed loop off above 1250 rpm); about 150 rpm
  is typical for e-throttle CL idle. Closed loop stops above the AP/TP lockout (AP Main with e-throttle). The deadband
  stops correction within plus or minus its value (20 rpm at 800 means none from 780 to 820) and applies to CL
  solenoids, not steppers. The Decel Timeout starts when rpm drops into the lockout band, and closed loop returns only
  once it expires.
- `vendor-doc`: Idle Status names the hold in force: open loop, TP or APS above lockout, rpm above lockout, rpm
  timeout, speed above 10 km/h, start-up step, overrun cut, or anti-lag ISC override. When the holds clear, it waits
  about 2 s for steady rpm before closed loop resumes. The default crank position is about 80 % open. When idle hangs or
  hunts, log the status alongside rpm, TP and speed.
- `vendor-doc`: idle-ups are added to the base position (% duty for a solenoid, steps for a stepper). They are A/C
  (needs an A/C clutch output and a request input), fan, power steering (needs a DI), neutral/park, start-up (decays
  over 3 s from engine running; set by temperature in closed loop), and Hold Step, a dashpot applied while rpm drops
  back to idle (typically 2.0 % on a solenoid and 10 steps on a stepper; unused with e-throttle).
- `vendor-doc`: for a stepper the minimum clamp is the lowest base less the idle-up sum (40 - (2+6) = 32) and the
  maximum is the highest base. For a solenoid the minimum is the lowest base and the maximum is the highest base plus
  the idle-up sum (79+3+9+5 = 96). For e-throttle the clamps are the lowest and highest base. Other topics give a 10 %
  margin (see Disputed).
- `vendor-doc`: the help's closed-loop procedure starts in open loop, then runs closed loop with idle-ups zeroed and
  P 1, D 2, anti-stall 8 at every temperature. Starting cold, each time ECT reaches a base-table breakpoint and idle has
  settled, copy the Idle Position channel into that cell, then extrapolate the rest. Tune P with free-rev return tests,
  then D, and finish with anti-stall at about 5 x P. The open-loop procedure is warm-up enrichment first, then the base
  cells from a cold start as ECT climbs, then each idle-up once at operating temperature. On e-throttle, tiny throttle
  changes shift idle a lot.
- `vendor-doc`: the Bosch two-wire solenoid example runs at 200 Hz, with the throttle stop set so that 0 % duty idles
  near 400 rpm and the valve screw set so that hot idle needs about 50 % duty. It uses clamps of 10/90 %, an AP/TP
  lockout of 1.5 % (TPS spanned), an rpm lockout of 500, a start-up step of 10 and a deadband of 10 rpm.
- `vendor-doc`: big ignition steps between neighbouring low rpm and load cells make closed-loop idle oscillate, since
  spark moves idle speed strongly; keep the idle-area cells alike.
- `vendor-doc`: on e-throttle the engine should idle from the zero-pedal row of the throttle target table with ISC
  off, with the base position adding only the cold correction. ISC Offset is the % that idle control adds to the
  e-throttle base target.
### Idle ignition control
- `vendor-doc`: with idle ignition active (every lockout satisfied) the final timing is exactly the idle ignition table
  value. Temperature, knock and other ignition trims do not apply, so any temperature dependence must come from the
  idle strategy itself.
- `vendor-doc`: the usual axis is Idle Target Error, which is target minus rpm (positive when running slow). Put the
  base idle timing in the zero-error cell and keep the main table flat at the same value around idle for a smooth
  handover. The help's shape is 10 deg at zero error, 8 deg at -50 rpm and 14 deg at +100 rpm.
- `vendor-doc`: the suggested lockouts are rpm 1200, MAP 50 kPa, non-driven speed 5 km/h and TP/AP 1.5 % (see
  Disputed for the throttle figure).
### Idle loads and A/C
- `vendor-doc`: the fuel trims for A/C, drive and fan add a fixed number of ms whenever their condition is true, at
  every operating point and not only at idle. They exist in Traditional mode only.
- `vendor-doc`: in A/C clutch Basic mode the factory controller keeps the decision, and the clutch and A/C fan engage
  on request when over 400 rpm. Full mode adds conditions: the evaporator must be above its lockout temperature and the
  high-side pressure within its window (typically low 175 kPa, high 2100 kPa, evaporator 3 to 4 C; -10 C ignores it).
  Clutch Delay gives idle control time to add air before the load arrives. The clutch may be dropped at high TP, AP,
  MAP or injector duty. Take the pressure limits from OEM data.
### Electronic throttle
- Pedal and throttle each have main and sub sensors that must agree. Calibrate in setup mode, which disables safety
  checks and must not be driven, then return to on. Take PID gains, deadband, motor duty limits and frequency from the
  maker's data for the throttle body, not by experiment (`practice` tutorial 10.14; `practice` session 155).
- The target table (pedal by rpm) shapes torque delivery. Airflow is very non-linear in angle: one NA six made nearly
  full torque from about 30 % throttle at 2000 rpm. Spreading the first 0 to 20 % of plate across about two-thirds of
  pedal travel makes pedal track torque; full linearisation can feel dull on a low-powered car, so a compromise is
  common. Change targets gradually across rpm.
- `vendor-doc`: TP(Main) is the plate position and AP(Main) is driver demand; the sub tracks are only a cross-check.
  The main must be the full-range track, and main and sub must never be swapped. Where the sub track stops changing
  (about 60 to 70 % of travel on some Toyota and Lexus pedals, and near 70 % on Ford BA and Altezza bodies), enter the
  main % at that point as "sub 100"; otherwise enter 100 %. Only analog inputs 1 to 12 can be TP. Typical APS fault
  limits are 0.1 V and 4.9 V, with an error value of 0.
- `vendor-doc`: typical loop values (the defaults fit most bodies; change them only in ON-Setup) are a motor frequency
  of 500 Hz (range 200 Hz to 10 kHz; fixed at 500 Hz on the external module and plug-ins), a deadband of 0.1 %, gains
  P 7.00 / I 0.145 / D 25.00, and duty clamps of plus or minus 90 %. Across the bodies listed, D is large next to P and
  I is tiny. Positive motor duty opens the plate.
- `vendor-doc`: E-Throttle Target = Base Target + corrections such as the idle offset; comparing the two shows what
  idle control adds. Throttle 2 either follows throttle 1's target including every trim, or runs its own table with no
  trims. Up to three target tables can be chosen by DI, aux state, anti-lag or cyclic idle; 3 overrides 1 and 2, and 2
  overrides 1.
- `vendor-doc`: start the target table 1:1 with pedal. Give the zero-pedal row about 2.5 % near idle rpm as an idle aid
  but 0 % through mid-rpm overrun, so the car does not surge when the cut ends. Closing the throttle at the rev limit
  is an option on NA engines, though turbo engines get extra lag from it. The limp-home opening comes from the 5 %
  pedal row (see `quirks-control.md`).
- `vendor-doc`: cruise control acts only through the e-throttle and needs a fault-free, tuned e-throttle, driven wheel
  speed and a brake switch. Status Enabled means armed, not holding; Active means holding speed.
### Launch, anti-lag, gear cut, traction
- Anti-lag retard mode changes what a number means: relative adds degrees to base; percentage scales base (-100 % of
  30 deg gives 0, -200 % gives -30); absolute uses the value as final timing, with zero cells falling back to the main
  map (`practice` tutorial 10.10). Cyclic idle thresholds sit a few percent of throttle above the idle opening.
- Launch: one launch rpm armed by the clutch with about 1 s arming time; retard only above an rpm and throttle
  threshold so it does not stall at idle; ignition cut. Retard and cut build boost by burning in the manifold, which
  can harm turbo, catalyst and hydraulic lifters.
- Gear cut: 90 to 100 % cut with a maximum cut time; ending the cut on the digital input rather than a timer works at
  any shift rpm. Exit decay trades pick-up against driveline shock: zero decay cured a bog on drag launches, while a
  small decay extended gearbox life on clutchless sequential shifts (`practice` sessions 093, 186 and the launch
  session). A simpler flat shift uses a GP rpm limit keyed on clutch and throttle, set near the rpm the engine lands at
  in the next gear.
- Traction control computes slip as driven over undriven wheel speed and acts above a per-gear slip target.
### Launch control
- `vendor-doc`: the modes are Single Launch RPM (a switch, best on the clutch; Arming Time requires the input to be held
  before launch arms, so shifts cannot set it off), 2D table (rpm against non-driven speed; it disarms above the
  Disarming Speed), 3D table, and Latched for rolling starts (holding a momentary button freezes the limit at the rpm
  when it was pressed). Modes that use wheel speed require a non-driven speed source, and their ignition trim stops as
  soon as non-driven speed exceeds 0 km/h.
- `vendor-doc`: in the launch retard modes, Degrees offsets the normal timing (12 BTDC with -30 becomes 18 ATDC);
  Percent changes the timing by a share of itself (-300 % takes 10 BTDC to 20 ATDC); Degrees Absolute uses the value as
  the timing (-35 = 35 ATDC). Retard needs both the activation TP and the activation rpm to be exceeded. An optional 3D
  fuel trim manages EGT.
- `vendor-doc`: typical turbo launch timing is about 20 deg ATDC with an activation TP of about 85 %; NA engines use no
  trim. Set the launch rpm too low for the speed at first, then increase it. A 3D retard table (rpm by TP) allows light
  retard when staged and heavier retard at full throttle.
- `vendor-doc`: to pick a launch rpm for a target slip, take the zero-slip rpm = (km/h x DI speed calibration x
  un-normalised gear ratio) / 360, then multiply it by (1 + slip fraction). The help's case (calibration 260, ratio
  169.3, 25 km/h) gives about 3057 rpm with no slip and about 3424 rpm at 12 %. The speed must come from a wheel that
  does not slip, and low speeds want extra slip so the engine does not stall.
### Anti-lag and cyclic idle
- `vendor-doc`: anti-lag works through extra air (a bypass or an opened throttle), retard so the gas is still
  expanding as the exhaust valve opens, extra fuel to cool the exhaust, and ignition cut on alternate cylinders so
  unburnt mixture lights in the exhaust. It is not for long periods.
- `vendor-doc`: nothing happens until anti-lag is armed (by a DI, a virtual aux, or always). Armed anti-lag goes active
  above AL Enable RPM and AL Enable TP (Main). Once both fall below, it stays on for the deactivation timeout, which
  sets how long the turbo stays spooled after a lift. It is off below 500 rpm.
- `vendor-doc`: typical Degrees-mode tables hold retard of -25 to -50 deg over about 1500 to 7000 rpm below about
  30 % TP and 0 from half to full throttle, fuel of 0 to 10 % only where retard is used, and ignition cut in % of
  events (50 % is typical). Fuel lowers EGT, but turbo and manifold life still suffer. Retard, fuel and cut each have a
  Table 2 switched by a DI or virtual aux (for example a milder wet table 1 and a harder dry table 2).
- `vendor-doc`: AL ISC Override forces the idle valve position while anti-lag is active (cyclic idle has its own
  override), in the solenoid or stepper idle modes only; stock idle valves rarely flow enough. With the e-throttle as
  the air source, use two target tables, with table 2 selected by anti-lag active, about 20 to 25 % throttle at zero
  pedal and rising to 100 % at full pedal. While anti-lag or cyclic idle runs, idle control and all other target
  corrections drop out.
- `vendor-doc`: cyclic idle caps rpm with cut when the driver lifts but the plate is held open (for rules that ban a
  bleed valve). Below Cyclic Idle Low TP the cyclic limit applies (about 1800 rpm is typical), above High the normal
  limit applies, and between them it is linear. Put Low about 2 % above the resting TP (resting at 20 % gives 22/26 %).
  The modes are Off, Always On, Cool Down (active for a timeout once anti-lag drops from active to armed, pumping air
  through to cool the exhaust) and On when armed. The advanced settings are a limit range (200 rpm is typical), start
  cut 30 % and end cut 90 %; a narrower range sounds harsher. The help disagrees with itself on several points (see
  Disputed).
- `vendor-doc`: the Group N example holds the throttle 15 to 25 % open, with anti-lag always armed, cyclic idle always
  on, and enable at about 3000 rpm and 60 % TP. For switch-only activation, set the enable rpm to about 500 and the
  enable TP to 0, so it is off while cranking and then runs until switched off.
### Traction control
- `vendor-doc`: slip % = 100 x (driven - non-driven) / non-driven. It is zero when the speeds are equal, +100 % with the
  driven wheels at twice the speed, negative under braking, and -100 % with the driven wheels locked. Slip can also be
  a table axis (GP rpm limit, boost reduction).
- `vendor-doc`: above the slip table value, a PID cuts torque (fuel or ignition % cut, plus retard) to hold slip there,
  so the value is the trigger and the target at once. The table is 2D by gear; 3D tables each take an allocation slot.
  Typical targets run from 3 % (hardly any slip) up to 10 % (enough to slide), less in higher gears. Atom and Monsoon
  lack it, and the per-gear values depend on gear detection.
- `vendor-doc`: the starting calibration is cut from 0 % (start) to 80 % (end), retard of -5 deg at the start and
  -20 deg at the end, and PID gains P 5, I 0.3984, D 0. The effective gain grows with the cut and retard spans, so
  retune the PID if they change; torque reduction that cycles points to bad gains. In the help's example (RWD turbo
  six, about 400 hp, road tyres), a 5 % target held through a full-power bend with about 10 to 15 % fuel cut and about
  10 deg retard. Fuel cut is the usual choice, because ignition cut sends unburnt mixture into the hot exhaust.
### Gear shift control
- `vendor-doc` (firmware 5.3.0 and later): gear shift control removes torque for upshifts (cut, retard, fuel trim) and
  adds torque for downshifts (a blip via the e-throttle or an actuator). Four shift types follow from the Drive/Overrun
  TP threshold and the request direction: above the threshold is a driven shift, below it an overrun shift. Requests
  come from up/down DIs, a lever strain gauge or a barrel sensor, and must last for the validation time (20 to 50 ms is
  typical). A clutch switch or H-pattern strain lever can identify only driven upshifts and overrun downshifts; the
  end-of-gears lockout and the maximum downshift rpm need a two-way (sequential) source.
- `vendor-doc`: the shift end modes are Time (per gear), Digital Input (lasts while the input is on) and Gear Barrel
  Position (ends when the next gear is seen, closed loop); Max Shift Time is the failsafe end for any shift. After a
  driven shift, cut, retard and fuel trim ramp out over the torque introduction time (0 = at once), and the
  reactivation timeout then blocks repeats.
- `vendor-doc`: dog boxes want a blip on overrun upshifts as well as downshifts, and the throttle trim is added to the
  present TP. The predictive blip end monitors rpm rise (a 40 to 80 ms response is typical) and needs a correct gear
  ratio table.
- `vendor-doc`: for an H-pattern box with a clutch switch, use the switch as the upshift DI with downshift off; a speed
  lockout stops clutch-in at rest from cutting, and a TP low lockout of about 80 % means only full-power upshifts cut.
  For a strain lever, the offset is the unloaded voltage (about 2.5 V is typical) and the gradient is set so a pull
  much harder than normal reads about 100 N, positive for up and negative for down. For a barrel sensor, Voltage
  Tolerance decides when the next gear counts as engaged. Gear Shift Count should step once per real shift; extra
  counts are spurious requests.
- `vendor-doc` (Gear Cut Control, 5.2.2 and earlier): above the activation rpm and TP the status reads Ready. When the
  DI comes on, it cuts ignition and retards the events that still fire. It ends on DI release or after the per-gear
  time, capped by Max Cut Time. Afterwards the cut ramps out, the retard is held for one cycle and then ramps out at its
  exit rate, and the enrichment is held for one cycle and then decays. Only DI 1 to 6 can be used. The drag starting
  values are activation at 4500 rpm and 80 % TP, cut 90 %, cut exit 10 % per 20 ms, retard -20 deg exiting 4 deg per
  cycle, enrichment 25 % exiting 4 % per cycle, and a cut period of 0.15 s.
### Nitrous and water-methanol
- Nitrous: dual fuel and ignition tables in overlay mode (zero outside the nitrous zone) triggered from a virtual
  auxiliary; values extend one breakpoint below the activation conditions so interpolation does not leave a partial
  edge. Chained virtual auxes must each require the previous one explicitly. With closed loop active, add a target
  overlay on the same aux or the trim strips out the added fuel (`practice` session 094).
- Water-methanol: tune without it first; when the kit is armed, offset tables remove port fuel to hold the same target
  and add timing (`practice` part 36).

## Disputed / conflicts

- **Rev limit cut type.** One course lesson prefers fuel cut where possible because ignition cut can harm some
  valvetrains; another practitioner usually uses ignition cut for GP limits; the help recommends ignition cut with group
  or auxiliary injection.
- **Boost solenoid frequency.** The help gives 20 Hz in one topic and 15 to 20 Hz in another; training agrees on 15 to
  20 Hz for common three-port valves.
- **Closed-loop idle speed lockout.** Training uses about 5 to 10 km/h. The help's speed lockout topic gives about
  2 km/h, and its idle status and closed-loop setup pages give 10 km/h; before 5.5.3 the lockout was effectively fixed
  at 2 km/h.
- **Oil pressure limit delays.** Training wants zero or a very short activation delay and a start-up lockout of a
  second or two; the help's GP RPM limit example uses a 10 s start-up lockout and a 3 s activation delay. Test: log oil
  pressure through start-up and hard transients, and size both delays from the trace.
- **Boost activation MAP.** Training places activation at about 100 to 110 kPa and 1500 to 3000 rpm; the help's setup
  guide uses about 2000 rpm and 80 kPa.
- **Boost stage 3 hysteresis and gains.** The course uses about 15 kPa; the help's setup guide uses 10 kPa, its stage
  description 15 kPa, and its example sets 10 to 30 kPa. The help's gain examples also range widely between topics
  (P 0.2 to 5), which it attributes to hardware.
- **Idle valve clamp margin (help against itself).** The clamp pages suggest about 10 % below the lowest and above the
  highest base value; the open-loop setup page uses the base extremes plus or minus the idle-up sum.
- **Overrun retard rate (help against itself).** The overrun setup notes call 5 deg/s a minimum; the settings page
  calls it a maximum, and its example of 15 deg in 3 s fits a maximum.
- **Cyclic idle (help against itself).** The setup notes give a 3 to 5 % TP gap between Low and High, and the High
  description gives 5 to 10 %. The anti-lag overview calls the cyclic limiter a fuel cut, while the advanced settings
  give ignition cut percentages. The overview says cyclic idle runs when anti-lag is off; the cyclic idle page says
  only while anti-lag is armed. Both say the two are never active together.
- **E-throttle loop values.** Training says to take PID values from the throttle maker rather than by experiment; the
  help says the defaults fit most bodies, tuning is only for when needed, and it lists per-body starting sets. These
  are compatible: the per-body sets are maker-style data to start from.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
