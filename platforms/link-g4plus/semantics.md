---
id: platforms/link-g4plus/semantics
title: How Link G4+ tables behave
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: []
supersedes: []
---

# How Link G4+ tables behave

Facts tagged `vendor-doc` come from the PCLink G4+ 5.6.8 help and apply to that version; the help outranks training
material on what a setting does. Points tagged `practice`, `practice` or `practice` come from training
sessions recorded on G4+ (and ViPEC, its twin of that era) and describe how tuners read and use the settings. Behaviour
that surprises people, and workarounds, are in `quirks.md`.

## Claim

A G4+ number only has meaning together with the mode that consumes it. In Traditional fuel mode a fuel cell is a
percentage of Master Fuel, scaled in the background by MAP (when Load = MAP) and by stoich/target (when the lambda
target is in the equation); in the Modelled modes it is an efficiency that the ECU turns into fuel mass from engine
capacity, injector data, fuel properties and charge temperature. Limit tables mark the end, not the start, of a cut
range; idle ignition tables are indexed by rpm error; closed-loop boost and idle run in stages with lockouts. Reading a
tune or a log correctly means resolving each of these before comparing a number with anything else.

## Why (derivation)

### Traditional fuel equation
- `vendor-doc`, `practice`, `practice`: pulse width before dead time is roughly
  PW = MasterFuel [ms] x (cell / 100) x (MAP / 100 kPa, only with Load = MAP) x (stoich / target, only with the lambda
  target in the equation) x the temperature and enrichment corrections. A cell of 100 at 100 kPa, uncorrected, delivers
  exactly Master Fuel. Doubling MAP doubles the pulse width with no table change, which holds AFR only if efficiency is
  constant, so the table is left to describe the efficiency shape.
- With the lambda target in the equation the ECU assumes the table was tuned to lambda 1 and multiplies by 1/target:
  0.82 gives about 22 % more fuel, 0.80 gives 25 %, and an AFR target of 13.0 on 14.7 stoich gives about 13 %. No sensor
  is involved; it is a feed-forward multiplier. The fuel table then becomes flatter and VE-like in trend, but its
  numbers are still not VE, because Master Fuel can scale them arbitrarily (`practice` session 011).
- With the target out of the equation, every target change is baked into the fuel numbers (higher peaks, lower floor)
  and the target table matters only to closed loop.
- Load = BAP corrects only for barometric pressure and is normally paired with a throttle-position table on engines
  without usable vacuum. The MAP/BAP crossover uses BAP below atmospheric and MAP in boost (`practice` tutorial 5.3).

### Modelled fuel equation
- `vendor-doc`, `practice`: the table is cylinder filling. The ECU computes air mass from capacity, MAP and charge
  temperature by the ideal gas law, then fuel mass from target lambda, stoich ratio and density, then pulse width from
  injector flow at rated pressure, differential pressure, dead time and the short pulse width adder. An error in
  capacity or flow therefore scales fuel directly.
- Charge temperature is a blend: 100 means coolant temperature, 0 means intake air temperature. Slow air at idle and
  light cruise picks up heat from manifold, port and valve after passing the IAT sensor, so the blend leans toward
  coolant at low airflow and toward IAT at high airflow (`practice` sessions 075 and the VE model session).
- The Fuel Charge Cooling Coefficient models evaporative cooling of the charge by the injected fuel. It mainly decides
  whether measured lambda follows a change in the target table; it also feeds background corrections.
- Fuel System Type tells the ECU how differential pressure moves with MAP, so a change of regulator type or base
  pressure needs only the new configuration, not a retune, if the model was set up properly (`practice`).

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

### Knock
- `vendor-doc`: Retard Gain is degrees removed per percent of knock level above threshold; Advance Delay and Rate set
  the return. The processing delay is 0.004 x rpm degrees on firmware 5.6.5 and later and 0.012 x rpm before; window
  start, length, retard limit and delay must fit between the two closest firing events. Retard is stored in
  per-cylinder trim tables, and Clear I-Trim Tables decides whether it resets at power-on.

## Assumptions

- PCLink G4+ 5.6.x firmware and help; Modelled modes need firmware 5.2.0 or later. Training sessions were recorded on
  various G4+ and ViPEC firmware of that era; where they disagree with the help, the help governs what a setting does.
- Spark-ignition engines on gasoline, ethanol blends or methanol.
- Training numbers are what one practitioner used on one engine, not limits or defaults to copy.

## Breaks when

- A tune from another generation (G4, G4X, G5) or a firmware outside 5.6.5 to 5.6.8: ids and behaviours can differ
  (see `quirks.md`).
- Modelled mode with poorly characterised injectors or a wrong capacity: the VE table absorbs the error and no longer
  transfers between injectors or targets (`practice` VE model session; `practice` session 089 found VE tables
  from three ECUs on one engine were not interchangeable).
- A fuel table tuned with odd target values in the equation: the table compensates and looks strange; turning the
  target function on or off after tuning shifts the whole tune.
- A turbo engine on exhaust back-pressure the model cannot see: mixture drifts rich at high boost and rpm even when
  the efficiency table is right at spring pressure (`practice` sessions 085 and 133).

## Practical use

### Fuel equation and table scale
- Three modes from 5.2.0: Traditional, Modelled, Modelled - Multi Fuel (`vendor-doc`). In every mode a higher number
  means more fuel. Equation Load Source and Fuel Table load axis are separate settings; Load = MAP is preferred.
  Traditional does not use Injector Flow at Rated Pressure, and those fields are hidden in that mode, though the dead
  time table is used the same way (`practice` session 087).
- Master Fuel (Traditional only) sets scale, not shape. Its job is to keep the table inside its range with fine
  resolution: the smallest keyboard step is 0.1, which is 1 % of a cell at 10 but 0.1 % at 100. A table whose biggest
  cells reach only 20 to 40 is coarse; one heading for the cap runs out of room. See Disputed for the target ranges
  each source uses. Rescaling is lossless: multiply the whole table by old/new Master Fuel.
- When starting blind, sessions pick a middle Master Fuel (12 to 14 ms in two sources), tune the shape, then rescale.
  For Modelled mode a flat 50 is the usual starting VE; for a Traditional table, look at the idle cells and pick a
  blanket value near them (`practice` Practical Standalone Tuning 8.115, 8.126).
- In Modelled mode enter the true capacity (allow for stroke or bore changes), Fuel System Type, base fuel pressure
  equal to the pressure at which flow was rated (it is also the fallback if the pressure sensor faults), density at
  20 C with its temperature coefficient, stoich ratio, charge cooling coefficient and minimum effective pulse width.
- Fuel Density guidelines at 20 C, in g/cc: 0.745 for gasoline, 0.789 for 99 % ethanol, 0.8077 for 95 % ethanol,
  0.791 for methanol. The
  temperature coefficient must be set whether or not a fuel temperature sensor exists (`vendor-doc`).
- Fill the target table with the real intended targets before tuning the fuel table, in either mode. Tuning to a
  target held in the head encodes the wrong air mass. Keep the target table on a pressure axis even when the fuel table
  is on throttle, so it still responds to boost (`practice` sessions 133, 163; `practice` 8.115). Beyond its
  last rpm column the target table holds the last value.
- Display in lambda rather than AFR when switching fuels; an AFR display with the wrong stoich setting misleads
  (`practice` tutorial 5.6).

### Load axis choice
- The help's example setups and the tutorial default use MGP (MAP minus baro) or TP, not MAP, on the fuel table axis;
  boosted engines in the courses use MGP with about 20 kPa spacing plus extra rows near idle and cruise vacuum (for
  example -70 and -50 kPa).
- MGP moves operation into a different row when baro falls, which models altitude for an NA engine at full throttle;
  sources dispute how well it models vacuum and boost (see Disputed).
- Throttle position suits individual throttles, big cams, or large throttle bodies where MAP barely moves (an NA K24
  with a 90 mm throttle, `practice` Civic part 1). Use fine breakpoints near closed throttle (for example 0, 2, 5,
  10, 15, 20 %) because most airflow change happens in the first few percent.
- A boosted engine with individual throttles needs Load = MAP in the equation under a throttle-position table: at one
  throttle cell boost can range from spring pressure to far above it. The baro/MAP crossover keeps the off-boost
  resolution problem and one session does not recommend it there (`practice` session 163).
- Breakpoints: rpm about every 500 with extras near idle-to-drive transitions (for example 750, 1250, 1750) and the
  last column a little past the planned limit; top the load axis just above planned boost. A four-corner table ran a
  VQ35 within about 1 kW at full throttle, which shows how much interpolation carries; resolution is needed only where
  efficiency departs from linear and where the car lives (`practice` EFI Fundamentals 5.3; `practice` fuel
  table resolution session).

### Fuel tuning order (help, Fuel Tuning Procedure)
Before tuning in any mode: confirm the fuel and engine settings, because some force a full retune if changed later;
zero or set known values in the correction tables and bring them in afterwards; and fill in the target table.
- Traditional: set up charge temperature correction first if used, set Master Fuel Trim to 0, choose Master Fuel for a
  usable span.
- Modelled: every fuel and injector figure must be right, not guessed. Configure the charge temperature table first;
  check that fuel pressure holds at the Base Fuel Pressure setting (set it with the engine running and charging, since
  pump output follows supply voltage, `practice` session 059); set the charge cooling coefficient before final
  tuning. Changing either later means retuning the VE table.
- Training order agrees and adds: injector data and short pulse adder before any fuel tuning; idle mixture via dead
  time before the VE table (small idle trims after a dead-time fix suggest the injector data can be trusted,
  `practice` Civic part 3); calibrate the charge cooling coefficient as one of the first fuel jobs; enrichments,
  transient fuel and cold corrections only after the warm base table.

Fuel System Type: None (no pressure correction, a last resort), MAP Referenced, Returnless (needs MAP), or FP Sensor
(needs fuel pressure and MAP sensors, and is the only one that supports a rising rate regulator). Without a fuel
pressure sensor the ECU assumes rail pressure equals the rated pressure entered.

### Charge temperature and charge cooling
- The blend table is always used in Modelled modes and optional in Traditional (zero it to get IAT-only behaviour).
  Sensor position matters: a sensor before the throttle may not represent the charge, and a heat-soaked manifold raises
  charge temperature (`vendor-doc`).
- Typical shape: 70 to 90 toward coolant at idle and low airflow, tapering to near 0 at high airflow. One session's
  VQ35 settled at 55 at 2000 rpm full throttle and about 8 to 10 at 5000 to 6000 rpm high load (`practice`
  session 075).
- Biased toward coolant at idle, the estimate swings by tens of degrees from cold start to hot, so the model does much
  of the warm-up work. Start the IAT fuel trim and warm-up table at zero and add only the residual; leftover IAT trim
  doubles the temperature response. A small closed-throttle enrichment at high IAT (3 to 5 % above about 50 C in one
  session) is used for hot restarts.
- Charge cooling coefficient test: in a steady cell in the injector's linear range, trim VE until measured equals a
  target of 1.00, then change only the target (to 0.90 or 0.95). If measured goes richer than asked, reduce the
  coefficient; if it falls short, raise it. Each change shifts base lambda slightly, so re-trim VE at 1.00 and repeat.
  Values that worked: 8 on a 2ZZ, 10 on another engine, 15 after one step on a turbo build; the default is 10.

### Injector data
- Dead time depends on battery voltage, differential fuel pressure and the drive type; typical just under 1 ms at
  3 bar and 14 V (`vendor-doc`). It is 2D on voltage by default and can be made 3D with differential pressure on the
  second axis, which a returnless rail needs because differential pressure moves with MAP (on a 350Z, rail 350 kPa
  while differential fell from about 420 kPa on a throttle blip). Use the differential pressure channel, not raw rail
  pressure (`practice` sessions 087, 147).
- Supplier data rarely matches the breakpoints: convert microseconds to milliseconds, enter matched points,
  interpolate the rest, and extrapolate below 8 V for a smooth curve; the 12.5 to 14.5 V band matters most.
- The short pulse width adder corrects non-linear flow below about 4 ms. Zero gives the old behaviour. Fill it from
  supplier data before any fuel tuning; adding it later changes idle and light cruise fuel. Without it, a kick upward
  in the lightest-load cells of an otherwise smooth table is that non-linearity, not real efficiency (`practice`
  sessions 011 and the short pulse adder session).
- Injector change, Modelled: enter new flow at the pressure actually run (for example 1180 cc/min at 400 kPa for a
  1000-class injector), dead time and adder; expect to land within a few percent and correct with one whole-table
  factor, then recheck high load. Only valid if the old table was truly on target with correct old data.
- Injector change, Traditional: Master Fuel x old/new flow, then dead time and adder; idle and cruise still need
  retuning because short-pulse behaviour differs between injector types.

### Staged injection
- Needs enough injector outputs; select sequential-staged (group-staged for batch); enter a separate secondary dead
  time table; primary data must already be right; power-cycle after enabling (`practice` part 35).
- The secondary/primary flow ratio is a starting figure only: rated flows are often optimistic and quoted at different
  pressures (nominal 2.9 worked as about 3.3 on an FD RX-7). If AFR goes rich as secondaries stage in, the ratio is set
  too low; lean means too high. Adjust in 0.1 to 0.2 steps against a primary-only baseline.
- Full-load staging value for equal pulse widths on both sets: 100 x R / (1 + R). A value of 50 splits fuel mass
  equally, which saturates the smaller primaries first and gives a step in delivery.
- A secondary pulse-width lockout (1.5 to 2 ms in one session) stops the ECU counting fuel from pulses too short to
  open the injector, which shows as a lean spike at staging. Staging accel fuel is a make-up pulse for a transport
  delay when secondaries sit far upstream; zero it first and add only if a lean dip appears. One injection timing table
  serves both sets (`practice` session 047).

### Injection timing
- Default is a single fixed angle (for example 330 deg), referenced to start, end or centre of injection, with a 2D
  table available. The split feature is for siamesed ports. Sweep test: lock pulse width, step end of injection in
  coarse steps, wait for equilibrium, and choose the angle where lambda settles richest (or closed-loop trim is
  smallest), since that means more of the fuel arrives burnable (`practice` session 061; `practice` RB25
  part 4).

### Start and warm-up enrichments
- Sequence: pre-crank prime (absolute ms), first-crank extra, cranking enrichment (held for a time), then above about
  400 rpm the engine counts as started and post-start enrichment (versus coolant, with hold and decay) runs until it
  falls to the warm-up value, then warm-up alone. Each stage's added fuel should step down smoothly; a later stage
  exceeding an earlier one points to an entry mistake (`practice` tutorial 10.2; `practice` session 051).
- Warm-up is best with one axis on throttle and the other on coolant (`vendor-doc`). Tune it only when post-start
  reads zero, with coolant sitting at a breakpoint; then tune post-start on restarts, scaling the whole table if it is
  uniformly off. Lambda good at first and then lean soon after start means post-start decays too early: lengthen the
  hold. The sources found Link's cranking and cold post-start defaults close (for example about 150 % at 10 C and
  110 % at 20 C cranking with about 40 % first crank).
- With the lambda target in the equation, a coolant offset on the target is a clean way to run richer while cold,
  because it changes delivered fuel by the right ratio (`practice` Evo 8 part 5). Never fix cold running in the
  main table, which represents the warm engine.

### Transient fuel
- Accel enrichment has Mode, Load Axis, Clamp, Sensitivity, Hold (in injection events, so its meaning depends on
  injection mode), Decay, Deadband, Cold Correction and Load Correction; Wakeup Enrichment is group fire only
  (`vendor-doc`). The help recommends TPS as the accel load axis.
- Shape in the sources: most enrichment from closed or light throttle, scaled down as starting MAP rises (1.0 at 0 to
  20 kPa tapering to about 0.3 at 80 kPa in one session), rpm clamp falling to zero by about 5000 rpm as port air speed
  carries the fuel, cold multipliers around 3 to 4 near 0 to 10 C.
- Reading a tip-in: clean first hit then lean drift means hold is too short (2 to 3 or 4 events); a rich dip after the
  hit means clamp too high or decay too slow. Closed-loop lambda is suspended during enrichment events, so the two do
  not fight. Optional transient ignition retard (indexed by TPS rate and rpm) exists for observed tip-in knock only.

### Closed-loop lambda
- A minor trim for driving; the help states it is not a tuning aid. Auto mode controls the whole range on the target
  table without dither; with two sensors it uses their average. Stoich Wideband dithers, has one gain, and allows
  per-bank sensors on V engines (`practice` session 086).
- Lockouts: coolant (so it does not fight warm-up), a start timer (about 5 s for sensor heat), rpm and MAP windows,
  and throttle and MAP rate-of-change lockouts (one lesson used 10 % or 10 kPa per 100 ms). A trim that drops to zero
  in part of the range is usually a lockout, not a fault.
- Gain: start at 2 to 3, double each test until lambda oscillates, then halve; more gain at larger error. Rate: about
  1 to 3 Hz from idle to 2000 rpm, 7 to 10 Hz near 6000 rpm and up; above about 10 Hz made control worse with common
  sensors in one session's testing.
- Trim limit: one symmetric value. About plus or minus 5 % over the full range in the sources; 10 to 15 % when used
  only at idle and cruise, where hot restarts need more.

### Ignition
- Ignition Delay compensates for signal path delay, which grows in crank degrees with rpm and otherwise gives a slight
  retard of a few degrees. Dwell must rise when voltage falls; not all igniters limit current, so excessive dwell can be
  harmful. Maximum advance hard-caps the total after stacked trims. Spark edge is falling for most systems and rising
  for some Honda, Ford and MSD setups (`vendor-doc`, `practice` tutorial 6.2).
- Above 8 cylinders, knock control and individual cylinder trims do not work correctly. Trailing split tables appear
  only with Engine Type set to Rotary.
- Fuel trims in extra compensation tables are percent of the main table; ignition trims are degrees, and several can
  be stacked (4D to 6D compensation, `practice` tutorial 10.4).

### Knock control
- Operates only above 500 rpm; reduces advance from internal detection or an external unit on a digital input; not a
  substitute for a correct map. Clear I-Trim Tables at power-on (the common choice) starts each drive fully advanced;
  off keeps stored retard, which then must be right. Window Start is measured after the ignition event.
- Filter: a narrowband centred on the bore-derived frequency is preferred for signal to noise (examples 6 kHz on an
  RB25, about 7 kHz on a 4G63); the 4 to 10 kHz wide band suits a flat-response sensor but picks up more noise.
- Threshold (target) table: armed but inert at its maximum of 1000. Log raw per-cylinder levels on knock-free low-
  timing pulls and set the threshold 20 to 30 % above that floor. Overall gain is set so knock-free noise near the rev
  limit at full throttle sits mid-scale (see Disputed). Per-cylinder gain can equalise cylinders that read loud on a
  shared sensor (for example 0.8 on one).
- Typical authority in the sources: retard limit 4 to 6 deg, return after 0.5 to 2.5 s knock-free at 0.5 to 5 deg/s,
  lockouts below some rpm and throttle. Needing more than about 5 deg of retard means the main table is wrong. Above
  the help's per-cylinder-count rpm limit detection can be wrong; set RPM High Lockout below it.

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

### Boost control
- Open loop outputs duty from the base table; closed loop drives duty toward a target table and needs activation
  thresholds and a timeout. The help recommends about 20 Hz for the solenoid in one topic and 15 to 20 Hz in another.
- Activation: rpm and MAP thresholds keep the solenoid quiet in vacuum (about 100 to 110 kPa and 1500 to 3000 rpm in
  the sources). A MAP threshold above what the spring alone reaches means control never starts; one too close to target
  leaves no time to manage the rise and overshoots.
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

### Electronic throttle
- Pedal and throttle each have main and sub sensors that must agree. Calibrate in setup mode, which disables safety
  checks and must not be driven, then return to on. Take PID gains, deadband, motor duty limits and frequency from the
  maker's data for the throttle body, not by experiment (`practice` tutorial 10.14; `practice` session 155).
- The target table (pedal by rpm) shapes torque delivery. Airflow is very non-linear in angle: one NA six made nearly
  full torque from about 30 % throttle at 2000 rpm. Spreading the first 0 to 20 % of plate across about two-thirds of
  pedal travel makes pedal track torque; full linearisation can feel dull on a low-powered car, so a compromise is
  common. Change targets gradually across rpm.

### Cam control and VTEC
- Use a preset mode where one exists. For inlet cams the most retarded position is the least aggressive; for exhaust
  cams the most advanced is (`vendor-doc`). VVT solenoids run far faster than boost or idle solenoids (250 Hz on a
  VQ35).
- Targets are advance from the cam's rest position found by the cam angle test, not a spec-sheet centreline (the test
  found about 158 deg ATDC rest on a K24). Increase test pulse count until readings settle; enter the lowest stable
  angle as the offset; turn the test off.
- VTEC: drive the solenoid from a GP output with AND conditions (rpm, throttle, coolant); use dual-table mode keyed to
  that output, not overlay, so table 1 is low cam and table 2 high cam. Dual fuel tables matter most; dual ignition is
  optional since 2 to 3 deg error still sits near MBT. Tune each table past the switch point so moving the switch does
  not create fuel errors. A cam phaser took roughly 0.1 s per 10 deg, so lead the VTC target ahead of the switch.
- Changes in required fuel when the cam is moved measure the cam's effect on filling, which works off a chassis dyno
  by comparing logged corrections (`practice` Civic part 5).

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

### Nitrous and water-methanol
- Nitrous: dual fuel and ignition tables in overlay mode (zero outside the nitrous zone) triggered from a virtual
  auxiliary; values extend one breakpoint below the activation conditions so interpolation does not leave a partial
  edge. Chained virtual auxes must each require the previous one explicitly. With closed loop active, add a target
  overlay on the same aux or the trim strips out the added fuel (`practice` session 094).
- Water-methanol: tune without it first; when the kit is armed, offset tables remove port fuel to hold the same target
  and add timing (`practice` part 36).

### Multi Fuel
Fuels can differ in stoichiometric ratio, density, viscosity, injector flow, target lambda, VE and cold start. Multi
Fuel also suits two similar fuels or two tunes on one fuel, switched by a dial. Setup: tune the first fuel on
unblended fuel in Modelled mode, use 3D prime, crank and post-start tables against ECT and blend, and set Warm Up
Enrichment to Multi-Fuel. Then on unblended second fuel, change to Multi Fuel, set the second fuel's flow, density,
coefficient, stoichiometric ratio and charge cooling coefficient, start the blend table linearly, and copy the target
table to Table 2 and adjust it. Use one rated pressure for both fuels' injector flow figures, and the blend table must
output 0 % on the first fuel and 100 % on the second. Do not assume E85 is 85 % ethanol. A second VE table
(Interpolate Between) is only needed for a large fuel change (`vendor-doc`).
- Training adds: tune the main fuel completely (fuel, ignition, boost, cold start, road check) before enabling Multi
  Fuel; copy every first table into its second before tuning; without real ethanol flow data enter the same flow as
  the first fuel; cranking enrichment rises most on ethanol (start about 1.4 times the gasoline values at the high-blend
  end); then test two or three intermediate blends. A lean result at E20 with a linear VE blend means more weight on
  table 2 there; knock at 10 to 30 % ethanol means less ignition blend.
- Boost and ignition can follow the blend; one view holds boost low until high ethanol, since performance users run
  high blends and low blends should favour safety (`practice` session 077).
- The flex sensor reports ethanol as 50 to 150 Hz for 0 to 100 % and fuel temperature as pulse width.
- Dual fuel (switching two complete table sets) is different from flex (continuous blend).

### Cylinder trims
- One fixed percentage per cylinder suits an imbalance that is constant across the map or EGT-based balancing (EGT is
  too slow for 3D tables: 10 % more fuel moved one cylinder's lambda from 0.91 to 0.86 at once while its EGT barely
  moved). Per-cylinder 3D tables, coarse and on the main table's load axis, suit per-cylinder lambda. On a V engine with
  one sensor per bank, put all of a bank's cylinders on one table and trim only the leaner bank (`practice`
  sessions 041, 064, 068).

### Triggers
A valid tooth count divides evenly into 360, and on a missing-tooth wheel it counts the teeth as if none were missing.
Arming threshold and filtering are advanced features; start at the lowest filtering, since filtering removes
information. A preset OEM mode configures both inputs, but sensor type, pull-up (on for Hall or optical), edge and
sync mode still need checking. Timing must be calibrated with a timing light after setup: lock timing, set the offset
at a steady idle (about 1500 rpm in two lessons), then raise rpm and adjust Ignition Delay until the mark stops drifting
(1 to 2 deg of drift by 6000 rpm is normal; large drift suggests reluctor polarity). An RB25 with a 24-tooth disc sat
at -344 deg and needed no delay change up to 5000 rpm (`practice` RB25 part 2).

### Direct injection
GDI capable units exist (such as the Force GDI). Do not guess pump control settings; those drives cap injector duty
at 50 % in hardware, and setting a saturated drive where Direct Injection mode is needed can damage the
injector.

### Tools
Quick Tune adjusts the main fuel table only, never ignition, and the help says it assists rather than replaces a
professional tuner. Tune ignition and boost control before using it. Quick Trim and closed-loop lambda are separate
functions. Mixture Map and Quick Trim need the fuel and target tables to have matching load sources set, or a load
value entered. Mixture Map gives each cell its average actual, target, sample count and error, and can apply a
correction. Closed-loop lambda must be off for Quick Tune, which has lockouts for coolant, load and rpm. "Load Centre
Tolerance" and "RPM Centre Tolerance" decide when a cell counts as centred.
- Settings used in one session: least filtering that removes jitter, a precision band about 0.01 lambda, about 1 s in
  the cell centre within about 10 % of the cell spacing, a minimum-load lockout so overrun cut is not "corrected", and
  a capped number of attempts (two or three usually converge). Tune-ahead copies a tuned value into the next cell up;
  add 2.5 to 5 % so the untuned cell arrives rich (`practice` session 082).

## Worked example

### Master Fuel rescale (Traditional)
A table peaks at 93 with efficiency still rising, Master Fuel 14 ms. Raise Master Fuel by 1.5 to 21 ms and multiply
every cell by 14/21 = 0.667: the peak becomes 62 and delivered fuel is unchanged. A course lesson did exactly this;
lambda flicked rich for a moment between the two edits, then returned to target (`practice` 8.130). Going the other
way, 25 to 14 ms multiplies cells by 25/14 = 1.786.

### Injector swap (Traditional)
290 cc/min to 1180 cc/min injectors with Master Fuel 15 ms: 15 x 290/1180 = 3.69 ms. If the field takes whole
milliseconds, enter 4 ms and multiply the table by 3.69/4 = 0.92. Then load the new dead time and adder data and retune
idle and cruise (`practice` injector retune session).

### Lambda target multiplier
A Traditional table tuned to lambda 1 at 100 kPa with targets in the equation. A boost cell targeting 0.82 receives
1/0.82 = 1.22 times the fuel, on top of the MAP ratio: at 200 kPa, a cell of 60 with Master Fuel 10 ms gives
10 x 0.60 x 2.0 x 1.22 = 14.6 ms before dead time and corrections.

### Staging value
Secondaries of 1600 cc/min, primaries 550 cc/min flowing like 480: R is about 3.3, so the full-load staging value is
100 x 3.3 / 4.3 = 76.7 %. With that value the log showed both sets at the same duty (67 %) at full load
(`practice` session 047).

### Charge temperature bias from two tests
At 2000 rpm full throttle, IAT raised from 30 to 60 C by heat soak: with the cell at 100 (coolant) lambda drifted about
4 % rich; at 0 (IAT) about 6 % lean. Zero drift lies 4/10 of the way from coolant toward IAT, so 100 - 40 = 60; a
follow-up test settled on 55. A lean trend means more coolant weight; near the answer, steps of 2 to 4 per test.

## Disputed / conflicts

- **Master Fuel target range.** The help aims for about 50 at mid rpm and load, 20 to 30 at idle and 75 to 85 at full
  power; a tutorial lesson aims for a maximum of 70 to 80; a course lesson 60 to 80; one session 80 to 90 at peak with
  idle at 30 to 40; another 75 to 95 for the largest cells; one practitioner on a boosted RB25 and an Evo 8 aims for 80
  to 100 near atmospheric with boost rising toward the 150 cell cap (`practice`). All agree on the purpose (avoid
  hitting the cap, keep resolution); the numbers differ with how much boost headroom is wanted. Discriminating test:
  does the highest expected cell fit under the cap with margin, and is a 0.1 step under about 0.3 % at idle?
- **MGP versus MAP as fuel axis.** The help and tutorial default to MGP for steadier AFR with baro; one training session
  analysed altitude and found MGP adds error in vacuum and on turbo engines, arguing efficiency follows the pressure
  ratio across the engine (intake over exhaust) rather than gauge pressure (`practice` altitude and elevation
  sessions). Test: log lambda error at the same rpm and MAP at two baro levels with each axis.
- **Traditional or Modelled.** The help and the course material favour Modelled for target and injector changes without
  retuning; one practitioner reports mixed results with Modelled on plug-in units and uses Traditional with Load = MAP
  except for flex fuel (`practice` RB25 part 1, opinion).
- **Why a second VE table on ethanol.** The help says a second VE table is only needed for a large fuel change; one
  session found the ethanol table 17 % higher at one bar on a Corrado (about 2 % at low load), blames model and injector
  error more than real charge cooling, and has never seen a flex setup that did not need one; the VE model session
  credits both real charge cooling and model error.
- **Secondary fuel properties.** The help warns E85 is not 85 % ethanol; one session enters E100 properties with a
  linear blend so home blends above E85 are not outside the range (opinion).
- **Charge cooling coefficient value.** Several training sessions treat it as an early calibration step; one session found the
  default close enough for most engines (about 1 % error); a session on another ECU argued that a simpler model a tuner
  understands can beat extra parameters.
- **Knock retard gain and authority.** The help and tutorial use 0.5 deg per percent; one session used 0.2, one
  practitioner 0.25. Return delay ranges from 0.5 s to 2.5 s and rate from 0.5 to 5 deg/s across sources.
- **Knock overall gain.** One session sets no-knock full-throttle noise at 400 to 500 of 1000, another at 500 to 600;
  both want mid-scale without saturation.
- **Knock window start.** The help measures Window Start after the ignition event and the tutorial example starts
  10 deg after spark; one practitioner describes the same default as opening 10 deg before TDC. Check the help for the
  firmware in use.
- **Rev limit cut type.** One course lesson prefers fuel cut where possible because ignition cut can harm some
  valvetrains; another practitioner usually uses ignition cut for GP limits; the help recommends ignition cut with group
  or auxiliary injection.
- **VVT coolant lockout.** The default had a 40 C coolant lockout; one practitioner disables it so a cold engine driven
  hard does not run parked cams against a fuel map tuned with cams active (opinion).
- **Boost solenoid frequency.** The help gives 20 Hz in one topic and 15 to 20 Hz in another; training agrees on 15 to
  20 Hz for common three-port valves.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
