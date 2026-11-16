---
id: platforms/motec/quirks
title: MoTeC quirks
layer: L3
confidence: low
sources: [vendor-documentation, practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: []
supersedes: []
---

# MoTeC quirks

- `vendor-doc`: M1 behaviour is package-specific. A table or channel in one package may not exist in another, so check the package and version first.
- No file parser exists, and this adapter has not met a real package or log.

Unless marked otherwise, the items below come from training material (`practice`, `practice`), shown on one M1 package (mostly M150 GPR/GPRP on a Toyota 86). Practitioner numbers are examples from those demos, not limits. Setting meanings are in `platforms/motec/semantics.md`.

### Pressure and unit traps

- M1 boost aim is gauge pressure; older MoTeC (M800/M100) and many other ECUs use absolute. Carrying an absolute habit into M1 asks for about one bar too much boost. Read any boost number together with which generation it came from.
- The "boost limit" tables are percentages of the span between boost activate and main aim, not pressures and not cuts. A session example: 70% in first gear with a 65 kPa aim and 10 kPa activate targets 70% of 55 kPa above activate. Use them to drop boost for wet settings rather than retuning the aim table.
- Wastegate duty table values are scaled between the min and max duty limits, so a requested 50 is the middle of the usable solenoid band (a session example band: 15 to 85%), not 50% duty. Numbers do not transfer to or from other ECUs.
- Solenoid polarity: an anecdote from one practitioner on older MoTeC software: an update added a parameter defining what 0% duty means, it ended up inverted, and the drag car made far more boost than intended and lifted a head. After any software or hardware change, confirm what minimum duty physically does, with a boost limit set, before a pull.
- With electronic throttle, the closed-throttle position can read around 14% because the ECU opens the blade for idle control. Calibrate pedal and throttle separately and confirm a smooth 0 to 100% sweep.

### Mixture aim and table interpolation

- The richest active mixture aim wins, so unused aim cells are filled with a lean placeholder such as 2.0. Interpolating from that placeholder delays engagement far beyond what the breakpoints suggest: in one demo an average-load aim of 2.0 at 140% and 0.78 at 150% did not go richer than the main 0.82 until about 149.8%. Place a less extreme neighbouring value or closer breakpoints when a gradual richening is wanted.
- Protection tables interpolate too. A coolant rev-limit table with 7500 rpm at 100 C and 3000 at 110 C starts pulling down just above 100 C. Fill unused cells above the main limit, since the lowest limit always wins.
- An average-load ignition trim keyed only to load average stays active after the driver lifts, because the average decays slowly, so add a MAP axis so it acts only in boost or at WOT.
- Inserted breakpoints: if lambda is right at two rpm sites but wrong between them, the breakpoint spacing is too coarse. A course inserts a new rpm site (auto-interpolated) and corrects only that column rather than spoiling the neighbours.

### Closed loop and Quick Lambda

- Lambda on target with closed loop running says nothing about the efficiency table. Read the trim: a session showed lambda on target while trim removed 7.5 to 8%, and another showed trims around +6% almost everywhere, meaning the base table was lean. Fold the trim into the table until trims sit near zero (a finished tune in the sources sits within about 2 to 3%, and 3 to 4% is treated as day-to-day variation).
- Trim pinned at its limit means the remaining error is not corrected: one session sat at a -15% limit and still ran 0.80 against a 0.90 aim after cams moved; another sat at 10% and was still 3 to 4% lean. Watch measured lambda, not just the trim.
- Pinned trim for the fault delay disables closed loop. Tight limits (such as 5%) can pin on a hot restart and drop closed loop just when it is wanted; a large cam change pinned a 10% limit, faulted, and lambda then drifted for the rest of the sweep.
- Quick Lambda often does not remove the whole error in one press; repeat it, or multiply the cell by measured over aim lambda by hand. The press works best held steady at the centre of a cell.
- One practitioner, usually sceptical of autotune, found this implementation good, especially with a CAN wideband feeding the ECU.
- Water-methanol: the GPR package had no fuel trim selectable by a switch input, so closed loop absorbed the methanol's extra fuel (trim moving from about -2% to about -13% at about 700 cc/min of 50/50 in one demo). That is a workaround that depends on wideband health and authority; the trim size does confirm fluid is flowing. A repurposed staged-nitrous trim is the cleaner route.
- Swapping to E85 on a correct model often leaves a uniform trim offset (about +5% at idle in one demo), attributed to an unmodelled injector viscosity effect; the practitioner scaled the whole efficiency table by the idle trim factor and then refined locally.

### Firmware, package and software behaviour

- Older firmware let overrun fuel cut stay active whenever the pedal was at zero, overriding cruise control and anti-lag. If those misbehave with overrun cut enabled, check whether cut is engaging and update the package.
- Minimum launch timing cannot be set positive; the highest is about TDC, which caused heavy popping on a small-turbo factory engine. Workaround: zero the launch timing P and I gains to disable launch retard.
- The launch function has no clutch input, only ground speed. A two-step is imitated with a two-site speed axis: 0 km/h holds launch rpm and 1 km/h holds the normal limit. Useful on 4WD where wheel speed is not a ground reference.
- Logged launch rpm sits above the launch table by the margin (control range); allow for it when comparing log to table. Too small a margin makes rpm oscillate between spin and grip.
- One firmware limited port end of injection to 120 degrees BTDC at the latest.
- An early Toyota 86 package referenced DI timing to end of injection, a port habit. Longer pulses pushed the start earlier until part of the fuel was injected during the exhaust stroke and adding fuel did nothing on the dyno. Check calculated start of injection never overlaps exhaust.
- Engine-specific locked packages come with factory trigger decoding fixed; rpm and position still need verifying.
- Rolling launch, throttle-based traction control, surge-bleed throttle control and similar functions shown in the sources ran on custom firmware, not standard packages.
- Single-cylinder air-shift engine: one practitioner's view is that a configured 100% fuel and ignition cut that still fails to release the dogs is probably not being applied as requested; check the logs and contact the supplier.

### Software (M1 Tune) and i2

- Wholesale changes to the supplied worksheets can set you back; one practitioner builds task-specific worksheets instead. Locked time graphs need the layout unlocking each session to edit.
- The M1 Tune time graph cannot filter a noisy channel live (an undamped exhaust pressure sensor, for example); filter afterwards in i2 and note the filter flag so it is not forgotten.
- i2 interpolates linearly between samples, so a slowly logged fast signal looks erratic or hides its peak. Examples in the sources: exhaust pressure at 10 Hz looked haphazard beside MAP at about 51 Hz, and a pre-throttle pressure spike on lift probably peaked higher than the 10 Hz trace showed. Rates in the sources: about 20 to 25 Hz or more for pressures, around 200 Hz for gear position during shift setup, 1 to 5 Hz for temperatures.
- i2 mixture map: plot lambda against rpm with colour by the same load variable as the fuel table (TPS for alpha-N, MAP for speed density), select the load bands of interest, apply a transport delay, exclude implausibly rich values and filter rpm change faster than a shift-like rate. If the load variable differs from the table's, you cannot tell which cells to change.
- i2 track map colour-coded by lambda in fixed bands shows where on track fuelling is off; read straights only, as braking zones show overrun values. Fix the lambda axis manually, since autoscale flattens the trace.
- Viewing rpm with filtering removed shows brief wheelspin blips (one session used them to decide which gear could take more boost).
- Summed best sectors overstate potential lap time; the rolling minimum is a more realistic target.

### CAN and devices

- M1 receive base ID is entered in decimal (a multiple of 16) while dash templates use hexadecimal: entering 16 in the dash puts the message on 0x16, not 0x10. Convert, and pick a base that does not collide with other traffic.
- A scale of 1 on a received channel gives wildly wrong values (lateral G reading -1 to -2 instead of about 0.01). The scale must equal the transmitter's resolution. The ECU field may display fewer decimals than the true value and still be right.
- MoTeC devices default to 1 Mbit/s. On a car sharing the factory bus at 500 kbit/s, the dash-ECU link goes at 500 and 1 Mbit/s devices such as expanders go on a separate bus.
- A MoTeC dash expresses CAN scaling as multiplier, divisor and adder, not a fractional divisor.
- Third-party widebands: the ECU accepts lambda over CAN only in its own lambda modules' format. Tuners decode the third-party template in a dash and retransmit it from the dash in MoTeC LTC format, so the ECU thinks it is talking to its own modules. Dash-mounted sensors (G, GPS) can be sent to the ECU the same way instead of adding sensors.
- The standard calibration on a MoTeC lambda-to-CAN unit tops out near 0.65 lambda; methanol targets richer than that need an NTK sensor and an extended rich calibration. One practitioner saw LSU 4.2 sensors die quickly on leaded race fuel and moved the same PLM to NTK sensors, which lasted far longer.

### Trigger and timing

- M800 reference/sync capture shows where the sync edge sits between reference edges; pick the edge combination that puts it nearest halfway. A sync relative position channel (50% is midway) can be logged; in one drag engine it drifted steadily with rpm through belt stretch until it crossed over at 10,000 to 11,000 rpm and the ECU cut out with trigger errors. Offset the sync from centre at idle to allow for the drift.
- Debounce rejects pulses shorter than a set width. Too much rejects real teeth on high-count or high-frequency inputs, and needing heavy filtering suggests a poor trigger system.
- Base timing check: older trigger systems can jitter 3 to 5 degrees at low idle; a course sets the offset with the engine held at 1500 to 2000 rpm where the mark is steady, and treats more than about 3 to 4 degrees of drift with rpm as a fault to fix.

### Base maps and protection gotchas

- Supplied plug-in base maps can carry odd values in cells not yet visited. An practitioner anecdote (M800, Evo 8 base map): a cut-like misfire at 7000 rpm at high boost turned out to be an individual cylinder trim of about -100% on one cylinder in high-boost cells; much time went into the ignition first, and scoping injector drive found it. Audit every trim and compensation table before tuning.
- Dyno oil temperatures are often lower than on track, so an rpm-based oil pressure minimum set close to dyno pressure trips falsely on track. Confirm with track logs.
- A lambda lean warning active near lambda 1 trips on every lift and overrun cut, and fast shifts give brief lean spikes; the sources key the lean limit to aim lambda, disable it near 1.0 and use a short delay.
- A raw knock-level warning fails because noise rises with rpm; warn from knock retard instead, which inherits the rpm-dependent threshold.
- Set a driver switch's fault default to the safe state (pit limiter off; a reduced boost multiplier for a power switch), and keep fault thresholds just outside the switch's real voltage range or a healthy switch reads faulty.
- For customer cars, explain protective rev limits, or the customer will report a misfire when one acts.

### Dash warnings and driver behaviour

- Dash warnings with time qualifiers, live values in the message, and escalating thresholds after reset are standard dash functions in the sources. Use only the outer shift-light LEDs for general warnings so shift lights still work.
- Two drag-car anecdotes from one practitioner show drivers stay flat through warnings when racing, so protection belongs in ECU actions, not only dash warnings.

### Disputed / conflicts

- Upshift cut depth: a single-cylinder demo configured 100% cut; another session calls 100% a common error and runs about 60 to 70% on turbo engines with post-shift retard (one practitioner's practice).
- Boost control: M1 sessions teach closed-loop PID on a tuned feed-forward; one practitioner prefers open-loop duty by gear and rpm on very high-boost M800 drag cars because a small overshoot matters there (stated as personal preference).
- Traction control actuator: a custom-firmware demo added proportional throttle closing and retard alongside cuts, with effectiveness unproven; a later session found DBW throttle too slow for top-level traction control.
- Pit limiter: throttle-only control was less accurate than cut-based speed limiting in one session; throttle capping is kept only as a maximum.
- E85 trim offset: correcting via a global efficiency scale (practitioner) versus the injector flow scaler (a suggestion put to him). On M1 the injector data includes a non-linear region beyond reference flow, so scaling reference flow alone would not shift flow evenly; he accepts either as valid.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
