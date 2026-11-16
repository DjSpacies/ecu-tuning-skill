---
id: platforms/link-g4plus/g4x-g5-notes
title: Link G4X and G5 notes
layer: L3
confidence: low
sources: [practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/link-g4plus/semantics, platforms/link-g4plus/quirks]
supersedes: []
---

# Link G4X and G5 notes

The adapter in this folder targets Link G4+ (PCLink 5.6.x). This entry records how the later G4X and G5 families behave in practice, as shown in training material, and where a G4X or G5 tune or log would need handling the G4+ parser does not give. Nothing here comes from the vendor help or from a G4X/G5 file examined by this project: every point is training-derived (tier B, mostly one practitioner's live sessions) and must be checked against the vendor help for the version in hand before it is treated as a platform fact.

## Claim
G4X and G5 keep the G4+ fuel, ignition and boost concepts (Traditional, Modelled and Modelled Multi-Fuel fuel equations; MGP or MAP load; dual tables; staged closed-loop boost) but add faster processing and logging, math-block channels, 4D/5D modifier tables, power management, normalised and per-cylinder knock modes, and reorganised menus (virtual outputs, aux assignment, idle ignition control). A G4X/G5 file cannot be read by the G4+ parser, and several values in it mean something different from what the G4+ adapter assumes.

## Why (derivation)
### What changed from G4+ (as the sources describe it)
- **Speed.** A side-by-side comparison showed injector pulse width reacting visibly sooner to throttle blips on G4X, credited to a faster processor; the practitioner links this to better transient fuel and spark and tighter closed-loop control (lambda, idle, boost, cam). Onboard logging is quoted at about 100 Hz on G4+ against about 1000 Hz on G4X, with more memory and a much faster download.
- **Math blocks.** G4X offers up to eight user equations built from existing channels, which G4+ lacks. They can be logged, displayed, or used as an axis for fuel, spark or boost tables.
- **Cam control.** The practitioner finds G4X cam control quicker to set up than G4+: manufacturer presets (for example a Honda K-series mode) bring tested PID gains, and a cam angle test in calibrate mode learns tooth offsets. A cold-oil compensation is mentioned for phaser response during warm-up.
- **Idle ignition.** The G4+ 3D table of idle error against ignition change is replaced on G4X by a simpler PID-style idle ignition control.
- **Virtual outputs.** On G4X the virtual aux page only offers off, test or on; the switching conditions are set on a general-purpose output whose function is set to drive that virtual aux. A G4+ user looking for a condition list on the virtual aux page will not find one.
- **Aux assignment.** The aux page shows a locked function; the assignment is made from the function's own setup window (for example the engine fan function chooses its aux output).
- **Closed-loop lambda update rate** tops out at 10 on G4X; the practitioner says G4+ allowed higher numbers, so a G4+ value does not transfer directly.
- **Knock.** A normalised mode judges spikes against the sensor's overall output pattern instead of a fixed threshold table; response can be spark, fuel or both. Per-cylinder gain and trim tables are available on boxes with a knock board (entry-level boxes lack one).
- **Traction.** Besides slip-based traction control there is a power management feature (race-timer target speed or open-loop reduction tables), and an onboard accelerometer can provide longitudinal g as an axis where no undriven wheel exists.
- **File interchange.** A G4X calibration file has one structure across all box types, plug-ins included, so a same-engine file from another box can seed a new base map with its trigger, cam and fuel setup; only the I/O pins need reassigning.

### How the fuel equations relate (shared with G4+, seen on G4X/G5)
- **Traditional** is an injection-time table: cell value times a master pulse width, then compensations. One course calls it a hybrid whose cells behave much like an unscaled VE table. With load set to MAP the ECU also scales fuel by MAP in the background, and with open-loop lambda correction enabled it scales fuel by the lambda target table, so the target table and the fuel table interact as in a VE model. A tuner who leaves the target table at placeholder values before tuning in this configuration bakes those placeholders into the fuel table.
- **Modelled** estimates air mass from displacement, cylinder count, VE, MAP (or the chosen equation load) and charge temperature, then fuel mass = air mass / (target lambda × stoich AFR), then pulse width from injector flow, fuel density, differential pressure, dead time and short-pulse adder. The master fuel number disappears because injector scaling lives in the injector setup.
- **Modelled Multi-Fuel** interpolates stoich, density and density temperature coefficient between the primary fuel (main fuel page) and the secondary fuel (multi-fuel page) by sensed ethanol content through a blend ratio table. The VE table is shared, so a Modelled petrol tune carries straight over; moving from Traditional to either Modelled mode means retuning the whole fuel table because the numbers mean different things.
- **Charge cooling coefficient** (default 10 in the sources) is a Link model term for the cooling effect of evaporating fuel on the charge. If it is wrong the model delivers the right lambda at the target it was tuned at but misses when the target is changed.
- **Charge temperature approximation** blends IAT and ECT by an airflow-indexed table: at low airflow the charge picks up heat from the ports and runs closer to ECT; at high airflow it approaches IAT. The right blend depends on where the IAT sensor sits.

## Assumptions
- Training material reflects the PCLink G4X/G5 versions current when it was recorded; no version numbers are given in the records, and menu names may have moved since.
- Most G4X points come from one practitioner's live builds on specific cars (K-series, SR20DET, RB25DET, supercharged and drag S2000). G5 points come from one course build (a 4G63) and one technical session on the charge cooling coefficient.
- The fuel-model descriptions assume port injection on gasoline, ethanol blends or methanol; the records do not cover direct injection on these boxes.

## Breaks when
- **Box tier.** A file moved to a lower-tier box (fewer I/O, no internal wideband controller, no knock board) silently drops the assignments that box cannot hold. Small boxes such as the Atom have only four aux outputs. Lower-tier injector drivers are saturated types rated around 2 A, so low-impedance injectors need ballast resistors, and paralleling several injectors on one driver (as done on an Extreme driving twelve injectors from eight drivers) needs a current check first.
- **Version mismatch.** Firmware older than the PC software can make outputs deviate from what the software commands. Updating takes a minute or two and must not be interrupted; a weak battery or a key cycle mid-update can corrupt the unit.
- **Unstored changes.** After a file is sent to the ECU, declining the store prompt means a key cycle reverts to the previous calibration. Some mode changes only populate their tables after store and a power cycle (an idle target table that did not appear until then is one example).
- **Base-file drift.** One anecdote: after a custom base file was uploaded the stoich setting read 14.1 instead of the 14.7 entered. Treat as a single observation, but it is why the sources audit key settings after every upload.
- **Plug-in base maps** start a stock donor car only: they assume stock injectors and no forced induction, have few strategies enabled, and on some chassis drive the dash through the serial port mode (a generic file can leave the cluster dead). One base file shipped with launch control active; another (a Honda DC5 map) had a single fuel table, and enabling dual tables gave table 2 a single scalar with no axes. The Link K-series base file had no VTEC off delay.
- **Analog lambda.** A mis-scaled 0 to 5 V wideband corrupts display, closed loop and lean protection together; a CAN wideband avoids the scaling step. With a narrowband, Traditional-mode closed loop chases a voltage and ignores the target table.

## Practical use
### Handling a G4X or G5 tune or log in this skill
- The parser reads G4+ `.pclr` tunes and `.llg` logs only. A G4X/G5 file uses a different software generation and has not been examined here: refuse it, ask for a CSV export or screenshots, and do not map its tables through `tables.yaml`. The G4+ quirks already note that one name can map to several DataIds across generations.
- Log rate can be about ten times higher than G4+. Resample before comparing with G4+ logs, and expect long logs to be large.
- Math-block channels are user-named and can be table axes. Do not infer what a math channel holds from its name; ask, or look for the defining equation. Common uses in the sources: uncorrected lambda (measured lambda with the closed-loop trim removed), target-minus-measured lambda or AFR for lean protection, MAP divided by exhaust manifold pressure as a fuel load term.
- Expect more tables per role: dual fuel and ignition tables switched by a virtual aux or the VTEC output, two cam target tables switched by VTEC, two boost target tables and two spark tables interpolated by ethanol content, 4D/5D fuel and ignition modifiers gated by a switch, gear or timer, and general-purpose boost sub-tables. A single "fuel table" is often not the whole story.
- Fuel table cells mean VE (percent cylinder filling) only in Modelled modes. In Traditional mode they are percentages of master pulse width. Read the fuel equation mode before interpreting any fuel number.
- Load axes: fuel tables in the sources are usually on MGP (MAP minus baro); Link base maps put ignition on absolute MAP. Alpha-N setups put fuel on TPS and may set the equation load source to baro. Check the axis channel of each table.
- Closed-loop correction reads zero when closed loop is locked out (TPS or MAP rate lockouts, startup delay, coolant lockout). Zero does not mean on target: compare measured and target lambda directly in those samples.
- The idle ignition channel on G4X comes from a PID controller with min and max clamps, not from a 3D error table.
- Wheel speed names are a trap. In this software "driving wheel speed" means the powered wheels and the other source is ground speed, but the practitioner's own wording swaps "driven" and "driving" between sessions. Confirm which physical sensor each channel carries before computing slip.

### Setup checks the sources run on these boxes
- **MAP calibration interlock.** The ECU will not fire injectors or coils until a key-on MAP-to-baro calibration has been done; run it and TPS calibration on every new upload, even on alpha-N engines where MAP is not the load axis. Close agreement (about 100.1 against 100.2 kPa in one session) confirms scaling and wiring.
- **Input pull-ups.** A Hall cam sensor (K-series) shows a cam signal error until the digital input pull-up is enabled. NTC inputs normally use the internal 1 k pull-up; turn it off when sharing the signal with a factory ECU.
- **Knock disable input.** If the knock-disable digital input is set to always on, knock control is bypassed silently.
- **Boost cut is relative to the boost target.** On a car running wastegate spring only, the practitioner still enables closed-loop boost with all duties and the minimum clamp at zero and a target near spring pressure, so the overboost cut has a target to compare against.
- **Staged closed-loop boost.** Control steps from a fixed pre-spool duty (stage 1) to a base-duty stage (stage 2) to PID (stage 3) as MAP closes on target; thresholds are per-tune settings (40 kPa in one tune; 100 and 15 kPa in another). If only stage 2 is allowed, duty latches at its last value when stage 3 would take over instead of following the base duty table; the practitioner's workaround is to allow stages 2 and 3 with PID gains at zero. Closed loop cannot run across two solenoids at once; with top and bottom port solenoids he runs the top one from a feed-forward table and the second open loop.
- **Closed-loop startup lockout** defaults to about 5 s; an external wideband may need about 30 s of heater warm-up, so the practitioner lengthens it.
- **Injector test** pulses continuously (2 ms at 10 Hz by default) until stopped. The pump is disabled, but residual rail pressure can still flood a cylinder; test with the injector out of the rail or use the advanced test with a fixed pulse count.
- **Communication.** Leave the connection speed on fast and drop to slow if the link drops out; set port and mode to auto. Page layouts are not saved automatically, and the software keeps only the latest save, so save staged copies of the calibration.
- **CAN.** G4X boxes terminate the bus internally at their end; a far-end 120 ohm terminator is still needed once several devices share the bus (one CAN wideband tolerated its absence, an AEM X-Series did not). All devices on one bus share a bit rate; transmit rates can differ. The Link keypad defaults to 1 Mbit/s and CAN ID 405, some other keypads to 500 kbit/s.

## Worked example
### Idle airflow check (Modelled mode)
At warm idle the practitioner read estimated air per cylinder of 0.12 g at about 920 rpm on a 2.4 L four-cylinder.
Air mass flow = rpm / 120 × cylinders × g/cyl = 920 / 120 × 4 × 0.12 = 3.7 g/s (3.7 × 10⁻³ kg/s).
His guide for a warm four-cylinder of that size is about 4 to 5 g/s, so the model is under-reading air: VE at idle is low, not the injector data. He multiplied idle VE by about 1.05 (to about 0.14 g/cyl, roughly 4.3 g/s) and closed-loop correction fell to about zero. Had the estimate sat inside the window with the mixture still off, he would have looked at dead time instead, since dead time is a large share of a short idle pulse.

### Reading a saturated trim
On an alpha-N ITB engine closed loop sat at its +20 % clamp with lambda still about 1.2 against a 1.0 target. The fuel the cell lacks is roughly (1 + trim) × (measured / target) = 1.20 × 1.2 = 1.44; the practitioner applied about 1.4 and re-logged. Where trim is not saturated and lambda is on target, the trim alone is the correction (+13 % gave 1.13 on a high-cam pull).

### Charge cooling coefficient step test (G5)
Closed loop off, injector data entered, a steady cell near 2500 to 3000 rpm and 60 kPa (outside the short-pulse region). Tune VE to lambda 1.0, then step the target in that area to 0.90. In a course build the engine reached 0.88: richer than asked, so the coefficient was too high. Halving it from 10 to 5 made lambda track; a technical session on an Evo 9 found the same change, with the default about 1.5 % rich at 0.90. Leaner than asked would mean raising it.

## Disputed / conflicts
- **When to calibrate the charge cooling coefficient.** The course and technical session do it before tuning the VE table, because changing it later shifts the whole table. The live-training practitioner checks it after VE and injection timing are done, with closed loop off. Discriminating test: change the coefficient on a finished table and measure how much steady-state VE correction it causes.
- **MAP-to-baro tolerance.** The practitioner quoted about 5 kPa as the most the calibration will absorb in one session and recalled 1 to 2 kPa in another; he flagged the second as uncertain. Check the vendor help for the version in use.
- **Traditional or Modelled.** The course practitioner tuned in Traditional and said either works the same once configured; the live-training practitioner defaults to Modelled for builds, suggests Traditional for beginners, and calls the choice preference. All agree flex fuel is easiest in Modelled Multi-Fuel; the practitioner shows a Traditional workaround (a 4D fuel table adding about 40 % at E100 plus a 4D spark table) that gets close.
- **Charge temperature model.** The course practitioner leaves charge temperature estimation off and uses a 3D IAT trim instead; the live-training practitioner uses the IAT/ECT blend table with about 15 % ECT bias at idle as a starting point.
- **Master pulse width in Traditional mode.** A course build on G4X aims for mid-map cells about 50 to 60 and a maximum about 80 to 90, and in another step rescaled to put cells near 40 to 50 at boost onset. The G4+ course and help figures in quirks.md aim for a maximum of 70 to 85. All agree the goal is resolution without running out of range, and that a whole-table rescale by old/new master value is lossless.
- **Pre-crank prime.** The same practitioner says in one lesson that the key-on prime is usually left off, and in a live session leaves it enabled.
- **Quick Tune.** The practitioner says Quick Tune needs a controlled environment where a cell can be held, so is impractical on the road; in another session he reports two or three Quick Tune drive cycles leaving little correction. His stated preference is manual log review or the mixture map fed with an uncorrected-lambda math channel.
- **Knock response.** The practitioner sets knock response to ignition retard only, in his experience fuel adds little. That is one practitioner's view; the platform offers both.
- **Stoich difference to ethanol.** The practitioner calls the petrol-to-ethanol change about 40 %; that is the drop in stoich AFR (9.0 against 14.7). As extra fuel mass for the same air it is about 63 %. Use the mass figure when estimating injector headroom.
- **Ethanol sensor fault default.** The practitioner defaults to about 85 % ethanol on the grounds that rich is the safer failure. This protects an ethanol-fuelled car; on a pump-fuel car it runs very rich, which is still the safer side. No source argues the opposite.

## Citations
- practice: Practitioner training and tuning practice, distilled and cross-checked.
