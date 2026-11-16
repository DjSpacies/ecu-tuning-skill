---
id: platforms/ecumaster/quirks
title: ECUMaster quirks
layer: L3
confidence: medium
sources: [practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/ecumaster/semantics]
supersedes: []
---

# ECUMaster quirks

How the EMU Black (and the PMU16 power distribution module) behaved on real cars in training material, and the traps
it sets. The main demonstration car was a JDM Subaru EJ20 turbo with quad AVCS. What settings mean is in
`semantics.md`. Tags `practice` and `practice` mark which training source showed the behaviour.

## Claim

The EMU Black's surprises are mostly about what is not where a tuner expects: changes vanish unless written to
permanent memory; timing lock left on makes the ignition table appear dead; first tooth and trigger angle together
cap the advance available; a boost-error duty table acts even in open loop; fuel and ignition share breakpoints;
the trim channel reads 100 % for no correction; the IAT table must start flat because the VE equation already
corrects density; and only two variable cams can be controlled. Reading a log or tune from this ECU needs those in
mind.

## Why (derivation)

- The EMU fuel equation uses VE, MAP and an air density term relative to 21 C (`semantics.md`). A traditional IAT
  fuel trim of roughly 2.5 to 3 % for every 10 C on top of it corrects density twice, so lambda drifts with air temperature in the
  opposite direction.
- Edits go to working memory; a power cycle restores the last burned copy.
- The trigger angle is the crank angle of the reference tooth before TDC; the ECU schedules spark from that tooth, so
  it cannot command more advance than the angle allows.
- Closed-loop trim is stored as a multiplier around 100 %, so values below 100 remove fuel.

## Assumptions

- EMU Black firmware and software of the period shown; the drive-by-wire calibration tool needs newer firmware.
- One engine family (EJ20) for most observations; VTEC and ITB remarks are from the same practitioner's sessions.

## Breaks when

- Later firmware may change table layout (separate ignition breakpoints, more cam outputs) or the DBW wizard.
- On a piggyback installation sharing sensors with a factory ECU, the input advice changes (pull-ups off).
- PMU behaviour is for the PMU16 configuration shown; other PDMs differ.

## Practical use

### Changes that do not stick or do not act
- On this ECU, write changes to permanent memory or they are lost on power cycle. This includes the pedal and DBW
  calibration (`practice` 8.26, `practice` 244).
- After the base timing check with ignition angle lock, turn the lock off and burn it. If not, ignition table edits
  appear to do nothing. Symptom in a log: ignition angle constant at the lock value (10 degrees in the demo)
  regardless of rpm and load (`practice` 8.29, `practice` 244).
- The ECU logs only channels selected in the log list. Without TPS in the log, later closed-throttle and transient
  filters cannot be applied (`practice` 292).

### Trigger and sync
- Choose first trigger tooth so the trigger angle sits above the maximum advance to be used: 45 to 60 degrees in the
  sessions (69 on the demo car). A 25 degree trigger angle would cap advance at 25 without any warning
  (`practice` 8.27, `practice` 244).
- VR crank: no pull-up, rpm-adaptive arming threshold, least filtering that triggers cleanly, since VR amplitude and
  noise both grow with rpm and too much filtering rejects real teeth. Triggering on the wrong VR edge shows as
  timing drift with rpm (`practice` 8.27, `practice` 244).
- Hall cam sensors need the pull-up. Do not allow sync without the cam signal and do not let cam sync be disabled
  above an rpm in the normal running range, so the engine never runs on a phase guess. Many Subaru variants use VR
  cam sensors; the JDM one shown used a three-wire Hall (`practice` 8.27).
- On an engine variant ECUMaster had not run, the suggested trigger setup failed and disturbed cam control until
  vendor support fixed it (one practitioner's experience). Expect to verify decoding on unusual variants
  (`practice` 244).

### Capability limits
- Only two variable cams can be controlled. On the quad-cam EJ20 the inlet cams were controlled and exhausts locked,
  costing boost response compared with the factory strategy; this shows as slower spool in ramp runs. Two cams
  cannot share one output to the same target because each needs its own duty to hold position. The unit also did not
  reproduce the Subaru CAN stream, affecting the dash and ABS/traction systems, and the TGVs were driven fully open.
  List every input and output the engine needs before choosing the ECU (`practice` 8.25, `practice` 244).
- Fuel and ignition share rpm and load breakpoints. Extra rpm columns added for a fuel-system quirk (3250, 3750) need
  not be tuned for ignition; fill them by interpolation between tuned neighbours (`practice` 8.33).
- With flex fuel using both tables, VTEC changeover was handled in one table by adding adjacent breakpoints at the
  switch point (4500 and 4501 rpm, and on MAP if needed) so each cam has its own cells (`practice` 244).
- An analog fuel pressure input showed steps of about 0.06 bar from A/D resolution; small apparent pressure changes
  below that are not real (`practice` 244).

### Fuel model
- Start the IAT fuel correction flat at 100 % and add trim only if logged lambda drifts at extreme air temperatures
  (`practice` 8.26).
- Closed-loop trim reads 100 % for no correction; below 100 removes fuel. A trim near 88 % at idle means the loop is
  pulling 12 % (`practice` 285).
- The autotune combines any existing closed-loop trim with the remaining lambda error when computing its correction,
  and lets the tuner inspect sample counts per cell and choose which cells to apply. The session applied 100 % of the
  correction when far out and 50 % when close (`practice` 285).
- Default closed-loop P and I from the manufacturer did not control well on the demo car: P 10 at idle overshot trim
  to about 112 %, I 5 oscillated wildly. A user who left high P on saw fuel dump to about 0.7 lambda. Start low,
  double until oscillation appears, then back off (`practice` 285).
- Closed loop may run from a cold engine (10 to 15 C) once the wideband is online, which helps trim warm-up; delay it
  after shift cuts and transients (about 100 ms starting point) so it does not chase the lean spike (one practitioner's
  view, `practice` 285).
- The onboard wideband controller failed to read an LSU 4.9 on one unit (probably a hardware fault) and an external
  CAN wideband was used instead. Controllers that read the sensor's calibration resistor are preferred over
  free-air calibration (`practice` 244).
- One practitioner deliberately removed 3 % for a measured 2 % rich error, from experience of how this ECU responds to
  a VE change (opinion, `practice` 8.34).
- Millisecond-based cranking and prime tables must be rescaled after an injector change; percentage warm-up tables
  usually need little change (`practice` 249).

### Idle and drive-by-wire
- The DBW idle range scales 0 to 100 % idle duty onto a maximum throttle opening (10 % on the demo). Choose it so
  running idle duty stays between about 10 and 90 %. Too small and the cold engine idles low; too large and
  resolution is coarse and closed loop has too much authority (`practice` 8.31, `practice` 244, 261).
- Tune the base idle table with idle PID off so closed loop cannot mask base errors (`practice` 8.31).
- Idle ignition control acts on rpm error from target, so it keeps working as the target moves with temperature.
  It advances toward MBT below target and retards above; it influences idle speed alongside airflow, so idle tables
  are revisited from a true cold start at the end (`practice` 8.31, `practice` 261).
- A radiator fan load correction of 10 % of idle range caused a flare each time the fan switched; about 5 % cured it.
  The same fan event pulled trim to about 88 % and lambda to about 0.87 before the loop recovered, which the session
  says belongs in a load-based fuel adder, not closed loop (`practice` 261, 285).
- After-start and idle-activation adders (rpm target and duty held then decayed) smooth the two known dip points:
  just after start and the moment idle control engages when stopping (`practice` 261).
- Pedal calibration: press firmly to the floor when sampling full travel (about 0.67 and 3.96 V on the demo). The
  DBW calibration tool (newer firmware, engine off) sets throttle end stops and derives PID gains (`practice`
  8.26, `practice` 244).

### Boost
- The EMU has a boost-error duty correction table that acts even in open loop, a passive feedback ahead of the PID.
  For first ramp runs, set open loop, zero that table, the PID terms and the wastegate duty table so the engine runs
  on spring pressure only (`practice` 8.34, `practice` 244).
- Overboost protection referenced to target (default 20 kPa over target at each rpm) protects a tapered high-rpm
  boost target that a single fixed cut set just above peak boost would miss (`practice` 8.28).

### Built-in dyno estimate
- The acceleration-based dyno function from a road log depended heavily on its filter (default unusably noisy,
  mid-teens smoothest, higher worse again), read about 270 hp against 316 on a hub dyno, misplaced peak torque and
  differed between gears. Use it for rough shape and run-to-run consistency only (`practice` 268).

### PMU16 power distribution
- Motor loads need an inrush limit with a short window and a lower running limit (30 A for 1 s then 15 A on a pump in
  the example), plus retries. Retries do not save a dead short, and a fuel pump retry interval of several seconds
  drops fuel pressure (`practice` 226).
- Undercurrent is only flagged, not acted on: the output keeps driving. A dry-running lift pump drew about 1 to 1.5 A
  against 4 to 5 A normally, but the minimum current setting does not stop it; custom logic on the fault flag is
  needed (one practitioner's account, `practice` 226).
- PWM outputs add heat in the PDM; balance high-current and PWM channels across the unit to avoid thermal shutdown
  (`practice` 226).
- Reserve pump logic shown: enable pump 2 when pump 1's output has been faulted about 1.5 s or fuel pressure has sat
  below a threshold about 1 s. The accelerometer inertia cut (6 g example) removes all power including pumps
  (`practice` 226).

## Worked example

Illustrative, built on the session's numbers. EJ20 at warm idle, closed loop active. The log shows lambda 1.00, trim 100 %, then the radiator fan switches on:
idle rpm flares well above target, trim drops to 88 % and lambda dips to 0.87 before recovering. Reading: the fan
idle duty adder is too large (it was 10 % of a 10 % throttle range, so about 1 % throttle). Halve it to 5 %. The
fuel dip is the load step, not a VE error; add a fan-linked fuel adder rather than widening closed-loop authority.
Re-log and confirm the flare and the trim excursion have both shrunk.

## Disputed / conflicts

- **Prime pulse.** One practitioner saw no need for it on the test Subaru and starts with it disabled, enabling it
  only for poor starts; it mainly helps injectors far from the ports. Base maps may ship with it on. Test: log
  cranking time to sync and first fire with and without it from the same coolant temperature.
- **Cold closed loop.** One session allows closed loop from about 10 to 15 C once the sensor is online; the common
  advice is to wait for full warm-up because cold engines want richer targets. Test: compare warm-up trims logged with
  each setting.
- **Shared fuel and ignition breakpoints.** The course treats them as a convenience; the cost is tuning effort when
  fuel needs extra columns. No discriminating test; a workflow choice.

## Citations

- practice: Practitioner training and tuning practice, distilled and cross-checked.
