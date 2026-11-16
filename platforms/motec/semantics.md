---
id: platforms/motec/semantics
title: How MoTeC M1 fuel and ignition behave
layer: L3
confidence: medium
sources: [vendor-documentation, practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: []
supersedes: []
---

# How MoTeC M1 fuel and ignition behave

Base facts come from the M1 GPRP Pro Setup and Tuning Guide and M1 Tune 1.5 help (`vendor-doc`), for those versions. Behaviour differs between M1 packages and firmware versions, so confirm the package first. Training material (`practice`, `practice`, `practice`) adds how tuners read and use these settings; it is tier B methodology, and where it describes a setting it was shown on one package (mostly M150 GPR/GPRP on a Toyota 86 FA20). Product traps and workarounds are in `platforms/motec/quirks.md`.

### Generations

- M800/M100-series (older hardware) uses a time-based fuel table: the main table holds injector pulse width against load and rpm, so injector size and dead-time errors live inside the table rather than in a model (`practice`). Its base pulse width, on the millisecond-style strategy, is the pulse at a table value of 100 at 100 kPa before compensations; it exists to give the table resolution, and a course starts it around 10 to 12 ms and revises it after first start (`practice`). Older MoTeC boost targets are absolute pressure.
- M1 (M130/M150 and others) runs a physical model. The rest of this file is about M1 unless it says otherwise.

### Fuel model (M1)

- `vendor-doc`: fuel is built on an engine-efficiency model. Engine Load, the mass of air per induction, comes from the Engine Efficiency table. Fuel Mixture Aim sets the target mixture. GPRP has adaption and sample tables for Engine Efficiency.
- Load axes: the efficiency table's load is manifold air density when a MAP sensor is fitted (or ambient density otherwise); ignition can use a separate normalised load axis such as MAP or TPS (`practice`).
- Inputs the model needs before any tuning: exact displacement (VE is a percentage of it, so a stroker must be entered), and fuel stoichiometric ratio, molar mass, reference density and its temperature coefficient (`practice`, `practice` agree). The package ships defaults for pump petrol, E85, E100 and methanol; race-fuel makers publish values for theirs. Intake air temperature is handled through the gas law inside the model, so there is no tuned IAT fuel table as on a millisecond ECU.
- Injector data defines the injector completely: reference flow and the pressure it was measured at, minimum reliable delivery, and a per-cylinder linearisation table giving pulse width for a wanted volume across differential fuel pressure and battery voltage, which covers dead time and the non-linear short-pulse region in the manner of OE characterisation. Per-cylinder tables even allow mixed injectors. Several sessions and a course agree that tuners cannot realistically generate this data and that wrong data corrupts the whole tune; buy injectors with a MoTeC characterisation file or have them characterised through a dealer.
- Fuel pressure: the measured fuel pressure is the pressure axis for the linearisation lookup, so it directly changes delivered fuel. On a returnless, non-referenced rail the ECU computes differential pressure as fuel pressure minus MAP from the two sensors (`practice`, Toyota 86 package at about 400 kPa fixed rail).
- Dual injection (FA20 D-4S package): DI is primary, port is secondary, with a secondary contribution (split) table. Each injector's rated flow is meaningless without its reference pressure (a course example: about 12.5 ml/s at 10 MPa for DI against about 3.3 ml/s at 400 kPa for port), and the DI injector has a hard minimum quantity (about 3 microlitres in that example) that the ECU respects.
- Mixture aim is an input to the fuel calculation, not a display, and the same table is the closed-loop target. Tuners from pulse-width ECUs often miss this. With correct injector and fuel data, the tuned efficiency numbers behave as a real engine property: a session demonstration changed aim from 0.85 to 0.90 and 0.93, and a lean cruise zone to 1.04, and measured lambda followed without touching efficiency. So set the aim table first to the targets actually wanted, then tune efficiency to match.
- Several mixture aim tables can be active (main, coolant, IAT, load average and others); the ECU uses the richest. A lean placeholder such as lambda 2.0 therefore disables a table's cells. Three sessions show this.
- Charge cooling gain models evaporative cooling, which scales with fuel quantity. One session treats it as a fudge factor in a general model rather than a measured temperature drop; on the DI demo engine it needed about 63 against a default of 38, while port engines tend to land nearer the default. Because changing it shifts mixture everywhere, it is set before the efficiency table and before transient work; if set later, changes to aim are no longer tracked correctly.
- Swapping injectors or fuel on a correct model: loading the new injector file, or the new fuel's properties, should land very close, with small touch-ups expected. This only holds if the original tune had injector and fuel data right.

### Start, warm-up and transients (M1)

- Two separate warm-up mechanisms: compensations to mixture aim (richer target on start, high coolant, high IAT) and fuel volume trims. Cold engines often need more fuel than the model computes because fuel wets port walls and arrives in a less combustible form, so changing the aim alone is not enough.
- Post start enrichment is a coolant temperature by run time table. A session extends it to 80 C and above for up to about 30 s to cover hot restarts after heat soak, and tapers it to zero within about 10 s when cold.
- Cold aim example from one session: about 0.88 at 0 C rising to 0.98 at 50 C, with a 2.0 placeholder from 60 C handing control back to the main aim. On a millisecond ECU the same richening has to be built into warm-up enrichment instead.
- M800/100-series option: the cranking table can use the engine temperature fuel compensation output as its axis instead of raw temperature, tying cranking fuel to the tuned warm-up correction (one practitioner's view; plain temperature is also valid).
- Fuel film model: a default film-against-MAP table shape that is broadly similar across engines, plus an overall scale value and a secondary-injector scale. The simple method resets all film tables and trims to vendor defaults and adjusts only the scale. The model uses MAP only, so a slow MAP signal degrades transient fuelling; a steady-state MAP-against-throttle estimate table lets the ECU use estimated MAP during fast throttle movement.

### Closed-loop lambda (M1)

- Quick Lambda (`vendor-doc`) corrects a site from current lambda and that site's aim. It can also transfer the current closed-loop trim into the efficiency cell so the trim returns to zero. Tuned cells are flagged and excluded from smoothing and interpolate functions.
- Trim limits are tables over rpm and load. Setting both limits to 0% disables control in that region. A session shapes them as about plus or minus 15% to 3000 rpm and 60 kPa, about 10% in overrun and high-speed cruise, about 5% in boost; another uses up to 25% at idle and 5% at WOT; a third limits WOT to about 5%. The common reasoning: model errors are largest from heat soak at idle and cruise, while large authority at high airflow could hurt the engine if the sensor misreads.
- Fault delay: if trim sits at its limit for the fault delay (60 s in a demo), the ECU declares the sensor faulty and disables closed loop. On dual-sensor V engines one bad sensor first drops control to single-sensor before full disable. Watch the closed-loop diagnostic channel.
- Gain is the fraction of error corrected per update (50% means two updates to remove an error, 100% one).
- Period is a table against exhaust mass flow, which the ECU computes from the modelled inlet mass flow. Transport delay falls as flow rises. A demo idles at about 2 g/s with a 2 to 2.5 s period and tolerates 150 to 200 ms at about 260 g/s (7400 rpm on the FA20); one tuner sized the axis to 350 g/s after logging a full pull.
- A delay table sets how long to wait after a trim change before re-evaluating.
- A coolant threshold gates closed loop (50 C in a demo). A long-term average trim feature exists and was left disabled in that demo.

### Ignition and knock (M1)

- `vendor-doc`: the torque model assumes optimum timing has been tuned in Ignition Timing Main.
- Ignition tables can be switched A to B by a driver switch input; a session uses this for water-methanol (B carries extra timing where fluid is sprayed).
- Knock (M150 GPR): four monitor frequencies are set, but only channel A drives control; the others are for logging. Thresholds are a table against rpm (and load) because background noise rises with rpm, while knock frequency itself changes little with operating condition. Control retards per cylinder, by an amount set by gain, then decays the retard back; a configured maximum caps it (5 degrees in one demo). A second-harmonic setting may be used when the fundamental is noisy.

### Boost control (M1)

- Aim is gauge pressure (manifold minus measured baro), not absolute. Error is computed against measured baro, so an aim and an absolute MAP that look 100 kPa apart still show a small error unless baro is exactly 100.
- An optional boost pressure sensor in the charge pipe before the throttle can be used; without it the ECU uses the manifold sensor.
- Boost activate is a positive-pressure threshold below wastegate spring pressure (MoTeC suggests about 10 kPa gauge). Within the margin below aim the ECU applies full duty to spool; above aim by the margin it drops duty to zero.
- Boost maximum is an overboost fuel cut that also disables boost control, with hysteresis before re-enabling.
- "Boost limit" tables (gear, EGT, IAT, coolant, switch and others) are not cut limits: each scales the aim as a percentage of the span between activate and main aim, and 100 means the main aim unchanged.
- Wastegate duty min and max are set to the solenoid's usable band; the 0 to 100 table values are then scaled between them, so 50 means the middle of the usable band, not 50% duty. Polarity is a setting.
- Final duty is feed-forward plus P (%/kPa of error), I (accumulated error) and D (%/(kPa/s)); the units beside each gain show what it acts on.
- Launch boost aim of zero effectively disables control, leaving spring pressure.
- A baro axis on the aim is possible, and custom builds have added IMAP/EMAP or ambient pressure as fuel-table axes (see quirks for how such tables read).
- M800: wastegate duty tables are by gear and rpm, and gear zero (neutral) is a usable row for duty while on the two-step.

### VNT, cam and throttle actuators (M1)

- An electronically actuated VNT uses a duty-to-position linearisation whose ends a session maps to the OE system's logged minimum and maximum vane positions rather than full travel.
- Cam control is aim against actual per bank with PID and a feed-forward hold duty; each bank of a twin-cam engine usually needs its own hold value.
- DBW throttle control has its own safety subsystem that typically cuts throttle output and applies an rpm limit on large tracking error.

### Idle (M1)

- Air actuator and ignition work together. When air feed-forward is right, timing sits near its idle target (12 degrees in a demo). A minimum timing limit caps retard, the main ignition table at the idle cell caps advance, and a ramp rate plus soft PI govern movement.
- Idle throttle aim maximum caps opening in idle mode and also scales the feed-forward table (table values are a percentage of that maximum). Too high costs resolution; it must still cover a stone-cold idle.
- Load adders (A/C, power steering) are feed-forward additions.
- On returning to idle the ECU adds an offset to the target, holds it for a delay, then ramps down to target, which reduces undershoot after a blip.

### Overrun (M1)

- Before cutting fuel the ECU can ramp timing toward a retarded target (a default rate of 30 deg/s toward about 10 degrees ATDC in a demo), then cut; on throttle reapplication timing returns even if the target was never reached. Fuel cut normally has an activation delay.

### Protection and speed limits (M1)

- Every protection and speed-limit function produces an rpm limit, and the lowest active limit wins. Fill unused table cells above the main limit so they never act, and remember tables interpolate between breakpoints.
- Warning functions take min/max values, hysteresis, an activation delay and a limp rpm limit. A lambda maximum can be a table against aim lambda.
- Engine load average is a rolling average with a time constant (1 to 30 s demonstrated) that can drive ignition trim, mixture aim, boost limit, throttle limit or rev limit. Race time is a conditioned timer with reset conditions, used the opposite way to permit aggression for a short window.
- If the gear sensor fails, the engaged gear can be inferred from wheel speed against engine speed through the stored ratios, so wheel speed data (for example from ABS over CAN) gives a fallback.
- Fuel margin on any cut-based limiter: a negative margin makes fuel cut lead (full fuel cut before the ignition cut range starts), a positive margin makes ignition cut lead.

### Launch, traction, pit limit, anti-lag and shifting (M1)

- Traction control computes the rpm the engine should run at from undriven wheel speed, tyre circumference, gear and final drive, adds the slip target, and cuts when actual rpm exceeds that traction limit. Cut ramps from 0 to 100% over a cut range that adds on top of the slip target, and fuel margin decides which cut leads. A minimum vehicle speed gates activation. Slip target can be compensated by lateral G against speed and by gear.
- Launch rpm is a table against ground speed; the function has no clutch input. Arming uses throttle entry and exit thresholds. Achieved rpm sits above the table by the margin (control range). Minimum launch timing is a retard controlled by P and I gains.
- Anti-lag tables are axised on throttle against rpm, with arming on throttle and delay, enable and mode switches, EGT and coolant shutdown and a timeout.
- Pit limiter (M150): modes are throttle-only, cut-based engine speed limiting, or combined, where cuts act as a backstop once speed exceeds target by an offset.
- Paddle shift (GPRP): actuator outputs, preload, re-arm and retry times, compressor control on a reservoir pressure sensor, gear position calibration with a per-gear tolerance, gear ratios, downshift rpm lockout, a power-on throttle threshold that separates cut shifts from blip shifts, and a shift timing table by shift type and gear. In closed-loop shifting the torque reversal time is a maximum: the cut ends when the barrel sensor confirms the next gear. Engine speed match is a percentage where 100 targets next-gear rpm and 0 current-gear rpm. An overspeed cut above calculated next-gear rpm backs up the blip.

### Direct and port injection timing (M1)

- DI timing is best referenced to start of injection, in degrees before compression TDC (360 is the start of the intake stroke), with an injection end limit (60 degrees BTDC in an FA20 session).
- Port end of injection was limited by one firmware to no later than 120 degrees BTDC.
- Staging DI with port: the secondary contribution must never reach 100% on DI, because the DI injector relies on fuel flow for cooling; the useful DI limit is pulse width (a rule of thumb of 6 to 7 ms at high rpm in one session), not duty. Matching duty cycles is the aim only for port plus port staging.

### Multi-throttle engines

- `vendor-doc`: a vendor technical note describes a method that avoids tuning the Engine Efficiency table directly, because of the variables involved. In practice it has the tuner work a manifold pressure estimate table instead (`practice`).

### CAN and inputs (M1)

- A receive template starts at a base ID entered in decimal that must be a multiple of 16, and spans up to 16 messages of 8 bytes. Each channel picks message number and byte offset (0, 2, 4 or 6), usually two bytes, four for high-precision data such as GPS position. A calibrated type takes a scale equal to the sender's resolution; a raw type ignores scale and needs a calibration table like a wired input.
- Analog inputs (rotary switches and similar) carry low and high fault thresholds with a time qualifier and a default value used on fault. Rotary positions are calibrated with an auto-calibrate key per position.

### Further facts (`vendor-doc`)

- Confirm a fuel composition sensor independently if a custom calibration is used.
- Batch-fire offset timing should not be used on direct injection.

### Disputed / conflicts

- Closed-loop gain: one session recommends about 80% as a starting value because 100% tends to oscillate; another found about 50% worked well on its car. Both agree a gain too high, or a period shorter than the transport delay, oscillates. Discriminating test: step the fuel at idle with the loop off to measure delay, set the period to it, then raise gain until oscillation begins.
- Closed loop at WOT: OEMs mostly run it only at idle and cruise, while one practitioner runs it across the whole map on CAN widebands that report warm-up and fault status, with tight WOT authority. Analog sensors without status make that riskier.
- Warm-up gating: one practitioner thinks disabling closed loop during warm-up is largely unnecessary with fast-heating CAN controllers; the demo still used a 50 C threshold.
- E85 reference density: one session quotes about 772 to 777 kg/m3, another about 782 kg/m3; use the fuel maker's data or the help file for the blend in use.
- Wall-film models versus rate-based enrichment: practitioners agree film models can transient-fuel better when calibrated, but are complex enough that most enthusiasts gain little over conventional tables (opinion).

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
