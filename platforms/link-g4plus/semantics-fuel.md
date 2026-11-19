---
id: platforms/link-g4plus/semantics-fuel
title: How Link G4+ tables behave: fuel, injection and lambda
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-17
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/link-g4plus/semantics]
supersedes: []
---
# How Link G4+ tables behave: fuel, injection and lambda

Part of `semantics.md`, which holds the overview, scope and sources; read it first. This file holds the fuel, injection and lambda settings and how they behave.

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
  0.791 for methanol. The temperature coefficient must be set whether or not a fuel temperature sensor exists
  (`vendor-doc`).
- Fill the target table with the real intended targets before tuning the fuel table, in either mode. Tuning to a
  target held in the head encodes the wrong air mass. Keep the target table on a pressure axis even when the fuel table
  is on throttle, so it still responds to boost (`practice` sessions 133, 163; `practice` 8.115). Beyond its
  last rpm column the target table holds the last value.
- Display in lambda rather than AFR when switching fuels; an AFR display with the wrong stoich setting misleads
  (`practice` tutorial 5.6).
- `vendor-doc`: the G4+ main fuel table holds at most 22 rpm columns and 20 load rows, at whatever spacing the user
  picks. Nearly every setup puts rpm on the X axis.
- `vendor-doc`: Master Fuel Trim multiplies Master Fuel by (1 + trim / 100), so +4 % on 9 ms gives 9.36 ms. A tune
  brought over from firmware that lacked the field should keep it at 0 %.
- `vendor-doc`: changing Fuel Equation Mode on a running tune forces a retune. Traditional is the quickest to set up
  and keeps the existing tune; Modelled pays off only when the injector, fuel and engine data are measured. The
  Modelled calculation is worked per cylinder, for one injector per cylinder (two when staged).
### Fuel properties
- `vendor-doc`: the stoich ratio converts air mass into fuel mass and sets the AFR display conversion. Typical
  figures: gasoline 14.7, ethanol 9.0, E85 about 9.7 to 9.8, methanol about 6.4 to 6.5, LPG about 15.5 to 15.8.
- `vendor-doc`: the density temperature coefficient, as a fraction per C, is about 0.00095 for gasoline, 0.00109 for
  ethanol and 0.00149 for methanol. Density is corrected for temperature only when a fuel temperature source is
  configured; with none, the ECU assumes 20 C. The source priority is an analog temperature input, then an analog volt
  input, then the ethanol sensor.
- `vendor-doc`: from firmware 5.0.0 the G4+ calculates in lambda and metric units and derives AFR from the entered
  stoich ratio. In Modelled - Multi Fuel, PCLink shows lambda whatever the unit setting, because a blend has no single
  AFR scale.
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
- `vendor-doc`: the help's crossover recipe for a boosted engine with little vacuum signal puts the main table on
  TP(Main), enables a 4D fuel table on an MGP axis whose first row is 0 kPa and all zeros, and puts the boost fuelling
  in the 4D table. Baro correction then covers the whole range, while the MAP term and the 4D table handle boost.
### Dual fuel table modes
- `vendor-doc`: Dual Table swaps the entire main table on an input or condition. Overlay works as a percentage
  overlay, like the 4D/5D tables; when no switching is wanted the help prefers it to those, because it is the larger
  table. Interpolate Between mixes VE tables 1 and 2 through a ratio table on an axis such as ethanol %, Multi Fuel
  Blend or analog voltage. It needs Modelled mode, and it can also bias VE with baro to account for turbo efficiency at
  altitude.
- `vendor-doc`: overlay and 4D/5D numbers are percentage changes to the main cell, so -10 % over a cell of 50 behaves
  like 45.
### Fuel tuning order (help, Fuel Tuning Procedure)
Before tuning in any mode: confirm the fuel and engine settings, because some force a full retune if changed later;
zero or set known values in the correction tables and bring them in afterwards; and fill in the target table.
- Traditional: set up charge temperature correction first if used, set Master Fuel Trim to 0, choose Master Fuel for a
  usable span.
- Modelled: every fuel and injector figure must be right, not guessed. Configure the charge temperature table first;
  check that fuel pressure holds at the Base Fuel Pressure setting (one session measures it running with the alternator
  charging, because the pump tracks voltage, `practice` session 059; the help differs, see Disputed); set the
  charge cooling coefficient before final tuning. Changing either later means retuning the VE table.
- Training order agrees and adds: injector data and short pulse adder before any fuel tuning; idle mixture via dead
  time before the VE table (small idle trims after a dead-time fix suggest the injector data can be trusted,
  `practice` Civic part 3); calibrate the charge cooling coefficient as one of the first fuel jobs; enrichments,
  transient fuel and cold corrections only after the warm base table.

Fuel System Type: None (no pressure correction, a last resort), MAP Referenced, Returnless (needs MAP), or FP Sensor
(needs fuel pressure and MAP sensors, and is the only one that supports a rising rate regulator). Without a fuel
pressure sensor the pressure term is built from Base Fuel Pressure, not measured (see Fuel system and pump control and
Disputed).
### Fuel channels for log reading
- `vendor-doc`: actual pulse width is the effective pulse width plus dead time. Accel, crank, post-start, warm-up, IAT
  and 4D/5D corrections are logged as a percentage of the base pulse width.
- `vendor-doc`: Load (Abs) follows the SAE definition: 100 % is a cylinder filled at atmospheric pressure and 200 % one
  filled at 1 bar above it. It is correct only with the true capacity and a calibrated MAP sensor. Mass per Cyl and
  Mass per Rev convert MAF g/s into air mass in grams per cylinder event or per revolution (x100 on screen), for use on
  MAF-based axes.
- `vendor-doc`: a Fuel Calculation Status of ERROR means a configuration fault, where settings or table values make the
  equation impossible to solve. It is not a hardware fault.
- `vendor-doc`: TP Delta Max holds the latest peak throttle rate long enough to read, then resets. Use it to place the
  accel enrichment, wakeup and knock rate lockouts. Prime Fuel keeps showing the prime delivered at the last start,
  whereas crank fuel passes too quickly to watch live.
- `vendor-doc`: the instantaneous fuel consumption channel is a Modelled-mode estimate. It is valid only for a
  four-stroke with one unstaged injector per cylinder, one injection per cylinder per 720 deg, and correct capacity and
  flow figures.
### Charge temperature and charge cooling
- The blend table is always used in Modelled modes and optional in Traditional (zero it to get IAT-only behaviour).
  Where the IAT is mounted changes what the blend has to correct, and the help's topics disagree on the best place
  (`vendor-doc`; see Disputed).
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
- `vendor-doc`: a colder charge estimate means denser air and a longer pulse, so blend values should fall as rpm and
  load rise. For a static check with ECT above IAT: richer than target means the estimate is too cold, so move the cell
  toward ECT; leaner means it is too hot, so move the cell toward IAT. Relog and repeat. Cold-start cells can take days,
  because the engine has to cool between attempts.
- `vendor-doc`: the IAT sensor has to see the air that reaches the cylinders. When boosted, mount it downstream of the
  compressor and intercooler; use an open-element type for response speed, and keep it away from hot spots in the
  manifold. The help topics disagree on the best spot (see Disputed).
- `vendor-doc`: a charge cooling coefficient of 0 turns that term off.
- `vendor-doc`: the Traditional IAT fuel correction is zero at 20 C, adds fuel below that and removes it above,
  usually with TP(Main) as its second axis so that it can vary with load. Without it, the engine runs richer than
  wanted when hot and leaner when cold. Switch the mode off when no sensor is fitted.
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
- `vendor-doc`: dead time must rise as battery voltage falls, or the engine leans out when voltage sags. The vendor's
  port-injector data shows about 0.3 to 0.8 ms at 14 V, roughly 1.5 to 3 times as long at 8 V, and a few tenths of a ms
  more going from about 40 to 80 psi. Use the data for the injector fitted; one figure does not hold across pressures.
- `vendor-doc`: for an on-car dead-time check, run fully warm with steady AFR and a trusted wideband. Pull the voltage
  down (alternator fuse out, or a load tester) and adjust the voltage table until AFR holds, keeping the curve smooth.
  Repeat after any injector or pressure change. A second check exists from 5.2.0: group fire at 1/2 cycle halves the
  effective pulse of each opening but still adds dead time per opening, so toggling between 1 and 1/2 cycle while
  running moves lambda only if the dead time is wrong.
- `vendor-doc`: the short pulse width adder is indexed on effective pulse width, with a secondary table that applies
  only when staged. The example ID1000-type data peaks near 0.17 ms at the shortest pulses and reaches zero by about
  3 ms. Firmware 5.6.5 onward applies it up to 8000 rpm.
- `vendor-doc`: Min Effective Pulse Width is the shortest primary pulse that trims may command, taken from the
  datasheet's minimum controllable pulse. Secondaries use Sec PW Lockout instead.
- `vendor-doc`: the injector test runs only at 0 rpm. The basic test fires 2 ms pulses at 10 Hz on each channel, for
  checking wiring. The advanced test, on drive 1, lets you choose count, rate and width (for example 30 pulses of 5 ms
  at 5 Hz, taking 6 s). The pump is off at 0 rpm, so run it from its aux test and switch that off afterwards. Volumes
  measured at two or more widths give flow per ms from the slope, and dead time from where the line meets zero flow.
- `vendor-doc`: keep injector duty below about 90 % at full power; above that, the injectors or the fuel supply are
  too small.
### Injector drives and wiring
- `vendor-doc`: injector drives switch the ground side, and +12 V must never reach a drive pin. Supply the injectors
  from the same 12 V feed as the ECU, so the voltage it reads for dead time correction is what the injectors get.
- `vendor-doc`: the impedance threshold is 6 ohm. Above it an injector counts as high impedance; below it, it needs a
  ballast or a peak-and-hold drive. Peak-and-hold (8 drives; peak to 10 A, hold 3 A) exists on Thunder, Xtreme and
  Fury, while Storm, Kurofune, Atom and Monsoon drive saturated only. The Force GDI drives direct injectors at up to
  75 V, with boost/peak 10 A and hold 5 A; its unused channels are not available as aux outputs.
- `vendor-doc`: the injector maker supplies the peak and hold currents; hold is usually about a quarter of peak (about
  4 A / 1 A at 2 ohm, 2 A / 0.5 A at 4 ohm). Use a 2.2 ohm ballast resistor when the injector is below 2 ohm and 4.7 ohm
  when it is 2 to 6 ohm, rated about 50 W on a heat sink, one per injector. A shared resistor makes the current depend
  on how many injectors are open.
- `vendor-doc`: a drive takes up to two high impedance injectors (one is preferred), wired in parallel, never in
  series. Drive current is the sum over coils of supply voltage / coil resistance; for example, three 12 ohm injectors
  on 13.5 V take about 3.4 A.
- `vendor-doc`: Active Drives (in group and group/staged modes) chooses how many drives fire; the remaining ones become
  aux outputs. Odd and even drives fire in opposite phase, so share the injectors evenly between them. Group/staged
  puts primaries on the odd drives and secondaries on the even drives.
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
- `vendor-doc`: the Sec/Pri ratio is summed secondary flow / summed primary flow. With four primaries of 240 cc/min and
  two secondaries of 650 cc/min it is 1300 / 960 = 1.354.
- `vendor-doc`: Sec/Pri Flow Ratio staging splits the computed pulse by the staging percentage (10 ms at 25 % becomes
  7.5 ms primary and 2.5 ms secondary, and the secondary share is then scaled by the ratio). Secondary Extra keeps the
  primaries at full pulse and adds a secondary pulse of staging value x primary effective pulse; the 5.0.2 notes liken
  it to an external extra-injector controller. Check the duty of both injector sets. Below the staging rpm lockout no
  staging occurs.
- `vendor-doc`: the shortest stable pulse can be up to about 1 ms longer than the dead time (in the example, 0.9 ms
  dead time and unstable below 1.6 ms). Below Sec PW Lockout the primaries carry all the fuel.
- `vendor-doc`: on sequencing limits, primaries and secondaries can both run sequential up to 4 cylinders. At 5 or 6
  cylinders the primaries stay sequential and the secondaries run as groups on drives 7/8. Engines of 8 cylinders and
  more need group staged.
### Auxiliary injection
- `vendor-doc`: drives 5 to 8 can act as four aux injection channels for extra fuel, nitrous or water. Each pulses once
  per engine cycle, at TDC 1 (Normal) or half a cycle later (Anti-Phase), from a 3D table in ms (0 to 25) or duty (0 to
  100 %). Optional extras are primary or secondary dead time, IAT correction and warm-up correction. A PW lockout drops
  pulses that are too short, and nothing fires at 0 rpm. Stagger the phasing to spread current draw and rail
  pulsation.
### Fuel system and pump control
- `vendor-doc`: the differential pressure used for flow is fuel pressure less MGP in Traditional. In Modelled it is
  zero with None, Base Fuel Pressure with MAP Referenced, Base Fuel Pressure less MGP with Returnless, and measured
  pressure less MGP with FP Sensor. The result is clamped above zero, and every type except None needs correct base and
  rated pressures (see Disputed).
- `vendor-doc`: the pump primes for a set time at key on (3 s is typical), then runs once rpm is seen. Two- and
  three-speed modes step up as injector duty or rpm passes each crossover (hysteresis 2 % duty). Three-stage PWM runs
  at 80 Hz with a duty of 33, 66 or 100 %, picked from injector duty; the status channel lists the middle step as 67 %
  (see Disputed).
- `vendor-doc`: open-loop pressure control derives pump duty from injector duty as table x multiplier + offset, then
  clamps it, aiming for a roughly constant return flow. Keep the minimum duty well above stall (most pumps stop under
  about 20 %) and cap the top (some controllers fault above about 95 %).
- `vendor-doc`: closed-loop pressure control is a PID on pump duty toward a target table, with feed-forward, clamps, a
  pump-off duty and a start-up override pressure. It needs a real pump speed controller (a solid state relay reacts
  too slowly) and a calibrated pressure sensor, and it suits a returnless system with a small bleed.
### Injection timing and modes
- Default is a single fixed angle (for example 330 deg), referenced to start, end or centre of injection, with a 2D
  table available. The split feature is for siamesed ports. Sweep test: lock pulse width, step end of injection in
  coarse steps, wait for equilibrium, and choose the angle where lambda settles richest (or closed-loop trim is
  smallest), since that means more of the fuel arrives burnable (`practice` session 061; `practice` RB25
  part 4).
- `vendor-doc`: the angle is in degrees BTDC of compression TDC, so 360 is overlap TDC, and it marks the end (most
  common), centre or start of the pulse. Port injection aims to finish just before the inlet valve opens, about 360 deg
  BTDC. Timing applies in sequential modes only. Rotaries always time the start of injection, 0 to 360 deg.
- `vendor-doc`: the split table (range -360 to +360) offsets every other cylinder in the firing order (on 1-3-4-2,
  cylinders 3 and 2), counted from each cylinder's own TDC, so odd-fire engines work. Tune it only with a per-cylinder
  measurement such as EGT.
- `vendor-doc`: semi-sequential is set up as Sequential with the injectors paired by firing order (1/5, 2/4, 3/6 on a
  1-5-3-6-2-4 six, which fuels one of each pair 120 deg early; about 72 deg on a V10). Unused drives still fire in
  their slot and cannot be reused.
- `vendor-doc`: on a four-stroke, group rate 1/2 cycle fires every 360 deg and 1 cycle every 720 deg. Since 5.2.0 the
  1/2-cycle rate halves each pulse, so fuel per cycle stays the same.
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
- `vendor-doc`: the pre-crank prime is a time from an ECT table (optionally 3D with ethanol %). Key On primes at every
  power-up. Ign Start Position primes the first time the key reaches start (it needs a start-position input), so fuel
  does not sit long before cranking. First Crank Enrich is separate and covers only the first revolution.
- `vendor-doc`: crank enrichment (on ECT, 20 cells 10 C apart, optionally 3D) acts below 400 rpm. Crank Hold Time
  keeps it going after the handover, so crank and post-start enrichment overlap at first.
- `vendor-doc`: post-start enrichment holds for Hold Time, ramps linearly to the present warm-up value over Decay Time,
  then leaves warm-up on its own. Decay is capped at 50 %/s, and a post-start value equal to warm-up skips the stage.
  Warm-up runs for as long as the engine does; its cells near operating temperature should be zero.
- `vendor-doc`: cold start and warm-up both run off ECT, so mount that sensor on the engine side of the thermostat. Use
  an An Volt input for 0 to 5 V sensors or where the factory ECU supplies the pull-up.
- `vendor-doc`: for a steady cold idle the help shows a 4D ignition table with an ECT axis from -40 C in 10 C steps
  against TP(Main) in 10 % steps from 0 %, with extra advance in the cold, closed-throttle corner.
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
- `vendor-doc`: accel enrichment is rate of change x Accel Sense, limited by the rpm clamp table, then multiplied by
  the load correction and the cold correction (1.0 when warm). The help's ceiling at 2000 rpm, 80 kPa and 20 C is
  55 % x 0.8 x 4.5 = 198 %. A clamp of 0 turns accel fuel off at that rpm. Cold correction multiplies the sensitivity
  as well as the clamp, and load correction also acts on wakeup widths.
- `vendor-doc`: decay is linear: after the hold, every event removes a fixed share of the original amount (50 % at 5 %
  decay runs 50, 45, 40, 35). Hold and decay count injection events, two per cycle in group fire and eight on a
  sequential eight, so revisit both after changing injection mode or moving a tune to another engine. Deadband is a
  rate threshold: a 1 % TPS deadband needs more than 1 % of movement from one sample to the next before it triggers.
- `vendor-doc`: wakeup (group fire only) fires a set number of asynchronous pulses at once, because ordinary accel fuel
  waits for the next scheduled injection. The width sits on top of dead time, moves from Low Width to High Width across
  the rate thresholds, is multiplied by the load correction, and stops above the End Point rpm (example 4000 rpm,
  4 pulses). It is most useful for small, quick openings at low rpm (a light tip-in at about 1200 to 1500 rpm in
  second). Its status reads Active when pulses were sent.
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
- Trim limit (training): a single symmetric value, roughly 5 % each way when closed loop covers the whole map, or 10
  to 15 % if it is confined to idle and cruise, where hot restarts want more. The help's typical figure is wider (see
  Disputed).
- `vendor-doc`: the lockouts the help calls typical are ECT about 5 C below operating temperature, a timer long enough
  for the start enrichments to end and the sensor to heat, MAP about 70 kPa, TP about 75 % and MAP delta about 4 kPa
  (Auto), with a stoich-mode gain of about 2. Keep the low rpm lockout below idle unless the engine idles badly at
  14.7:1 (see Disputed for rate lockouts).
- `vendor-doc`: closed loop is never active below 500 rpm. CLL Status gives the reason it is not trimming: an rpm, ECT,
  start timer, MAP, TP or rate lockout, launch armed, anti-lag, overrun cut, accel enrichment, Lambda Avg lacking a
  valid wideband, a silent narrowband (below 0.05 V for more than 15 s), the reactivation delay, or a clamp hit. A
  clamp hit means base fuel is further out than the trim allows. An OFF / Increase / Decrease channel shows whether the
  trim was acting over a stretch of log.
- `vendor-doc`: dual bank control exists only in the stoich modes, with one sensor per collector. Bank trims are
  applied through the individual cylinder fuel trims, on top of any user trims, with one shared set of lockouts. A
  second CL correction channel reports bank 2.
- `vendor-doc`: the final target is the target table plus the Open Loop Target Overlay table, added together (+1 AFR
  turns 14.7 into 15.7). The overlay moves the CLL target as well. Uses include cold running, safety richening and
  altitude.
- `vendor-doc`: narrowband stoich mode dithers about a set voltage (0.45 V is typical). A narrowband shows only rich or
  lean and is not a tuning tool. It needs more than about 300 C and can misread at very high EGT (turbo, rotary).
### Wideband inputs
- `vendor-doc`: Lambda 1 and 2 can come from an analog input, the internal controller or CAN; Lambda 3 to 8 come from
  CAN only. Each lambda parameter takes one source.
- `vendor-doc`: Lambda Avg is the mean of up to 8 sensors, excluding invalid ones (CAN 3 to 8 reading zero, internal
  or CAN lambda 1 to 2 outside Operating, analog beyond its error limits). Its value with no valid sensor is disputed
  (see Disputed).
- `vendor-doc`: the internal controllers (Fury, Thunder) hold an LSU 4.9 at 780 C, and a reading counts only in
  Operating status. Mount the sensor within about 60 deg of horizontal, where the exhaust stays below about 730 to
  750 C but the heater can still warm the sensor, and away from heavy back-pressure, which biases it. An unheated
  sensor must not sit in running exhaust.
- `vendor-doc`: the built-in analog calibrations cover very different spans (one puts 0 to 5 V at lambda 0.50 to 1.52,
  another at about 0.61 to 1.09). A controller whose output does not match the selected calibration skews every logged
  and closed-loop lambda. From 5.0.0 the Lambda 1/2 inputs are calibrated in lambda.
- `vendor-doc`: the internal lambda error channel shows only the highest-numbered active code. Useful groups: 13/35/36
  = calibration resistor; 16 = heater slow to reach temperature; 17/18 = pump-current protection (exhaust very rich or
  lean, or a failing sensor); 26 = low battery; 33 to 48 = wiring at pin level; 49/50 = overheating or low cell
  resistance; 54 = more oxygen than free air, so the sensor is likely bad.
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
- `vendor-doc`: the blend ratio table (0 to 100 %) blends only the stoich ratio, injector flow, density and its
  coefficient, the charge cooling coefficient and the lambda target. VE, ignition, warm-up and boost blend only where
  each is set to follow Multi Fuel Blend. Dual ignition tables may follow raw ethanol % instead, so timing need not
  track the fuel blend.
- `vendor-doc`: check intermediate blends at about every 10 % ethanol, adjusting the matching blend cell and
  rechecking cold start at each one.
- `vendor-doc`: the supported ethanol sensors (Link, GM/Siemens, Continental) all use the GM Siemens DI type. On a
  sensor error the fault value replaces the reading, so choose one that selects the safest tune. During the start-up
  lockout (fuel must reach the sensor first) the value saved at the last shutdown is used.
### Cylinder trims
- One fixed percentage per cylinder suits an imbalance that is constant across the map or EGT-based balancing (EGT is
  too slow for 3D tables: 10 % more fuel moved one cylinder's lambda from 0.91 to 0.86 at once while its EGT barely
  moved). Per-cylinder 3D tables, coarse and on the main table's load axis, suit per-cylinder lambda. On a V engine with
  one sensor per bank, put all of a bank's cylinders on one table and trim only the leaner bank (`practice`
  sessions 041, 064, 068).
- `vendor-doc`: per-cylinder fuel trims are percentages, either single values or up to eight shareable 3D tables (per
  V bank, or inner against outer cylinders). Staged modes trim the primaries only. Ignition trims are in degrees, with
  positive values advancing; the ITrim Cyl channels leave out knock retard.
### Direct injection (Force GDI)
GDI-capable units exist (such as the Force GDI). Do not guess the pump control settings. Those drives cap injector
duty at 50 % in hardware, and setting a saturated drive where Direct Injection mode is needed can damage the
injector.
- `vendor-doc`: direct injection works in Modelled or Modelled Multi Fuel only. Rail pressure comes from a cam-driven
  pump whose spill valve is timed to the cam. All pump control references the crank angle (after TDC 1) where pump-cam
  lift peaks, found with a dial gauge (on a VVT cam, fully home with the VVT channel linked).
- `vendor-doc`: maximum stroke volume = pi x (bore/2, cm)^2 x lift (cm). The calibration table has 16 cells mapping %
  of maximum flow to degrees before lobe centre, using % flow = (1 - lift / max lift) x 100 from the measured profile
  (100 deg before centre gave about 46 % on a 4.95 mm lobe). Spill valve dead times must be accurate.
- `vendor-doc`: rail pressure can fall only by injecting, so the target decay rate slows target drops. Control is PI
  plus a compensation table (usually rpm by fuel per cylinder). Tune that table until pump output % stays about
  constant, which allows lower gains. Check tracking with target steps at 3000 to 4000 rpm.
- `vendor-doc`: the GDI setup order is the low-pressure feed, then injector drivers and data, injection timing, the
  pump solenoid driver, pump calibration, error values, target pressure and finally closed loop. Injection should start
  roughly between intake valve opening and early compression; wrong timing can put fuel into the power or exhaust
  stroke.
- `vendor-doc`: the driver applies boost voltage (for example about 65 V) up to the boost current, then peak current
  for the peak time, then an off time, then hold current. Two injectors share each driver, hence the 50 % duty cap per
  injector; intake-stroke-only injection is about 25 %. Pair cylinders that never inject at the same time (on 1-3-4-2,
  1 with 4 and 2 with 3). Feed the 14 V converter straight from the battery through a 15 A fuse.

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
- **Charge cooling coefficient value.** Several training sessions treat it as an early calibration step; one session
  found the default close enough for most engines (about 1 % error); a session on another ECU argued that a simpler
  model a tuner understands can beat extra parameters.
- **Base Fuel Pressure measurement.** `practice` session 059 sets it with the engine running and charging, since
  pump output tracks voltage; the help's Base Fuel Pressure topic measures rail pressure with the pump on and the
  engine stopped. Test: compare engine-off rail pressure with idle while charging, on the car in question.
- **Pressure used without sensor.** Earlier KB text (training) said the ECU assumes rail pressure equals rated
  pressure; the help's differential pressure topic says MAP Referenced uses Base Fuel Pressure, Returnless uses Base
  Fuel Pressure less MGP, and None gives zero. These agree only when Base Fuel Pressure is set equal to rated pressure, as
  advised above.
- **Lambda Avg with no valid sensor.** The help's Lambda Average topic says it falls back to 1.0, so closed loop sees
  stoich and does nothing; 5.6.5 release notes say it falls to zero and closed loop is suspended. Either way no trim
  results, and a logged average sitting exactly at 1.0 or 0 may mean no valid sensor. Check on the firmware in use.
- **Quick Tune precision band.** One session used about 0.01 lambda; the help's example is 0.05.
- **Fuel pump PWM steps.** The pump control and aux allocation topics give 33, 66 and 100 %; the pump speed status
  topic lists 33, 67 and 100 %. The difference does not matter for tuning.
- **Closed-loop rate lockouts.** A course lesson used 10 % or 10 kPa per 100 ms; the help's typical values are a MAP
  delta of about 4 kPa and TP about 75 % (Auto). These are different examples, and both are kept.
- **Closed-loop lambda trim limit.** Training uses one symmetric limit: about 5 % either way when the trim runs over
  the whole map, and 10 to 15 % if it is kept to idle and cruise. The help's lockouts and limits topic gives about 15 %
  either way as typical, with no idle-and-cruise condition, and the 5.6.8 release notes list a fix to 3D closed-loop
  trim limits, which suggests a table-based limit in some 5.6.x builds. The help governs what the field is; read it in
  the tune's firmware before relying on either.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
