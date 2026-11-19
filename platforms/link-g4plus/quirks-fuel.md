---
id: platforms/link-g4plus/quirks-fuel
title: Link G4+ quirks: fuel, injection and lambda
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-17
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/link-g4plus/quirks]
supersedes: []
---
# Link G4+ quirks: fuel, injection and lambda

Part of `quirks.md`, which holds the overview, scope and sources; read it first. This file holds the fuel, injection and lambda gotchas and workarounds.

## Practical use

### Fuel model traps
- Turning the lambda target function on or off after tuning shifts the whole tune, because it adds or removes a
  background multiplier.
- Changing Master Fuel shifts AFR everywhere unless the table is rescaled by the inverse.
- The traditional fuel cell caps at 150 in one practitioner's RB25 tune and several sources treat 100 as a practical cap
  on other units; if cells hit the cap and still need fuel, raise Master Fuel and rescale.
- Changing the charge cooling coefficient or the charge temperature table after the VE table is tuned invalidates the
  VE table.
- Injector flow and rated pressure fields are hidden in Traditional mode.
- psi breakpoints in the dead time table snap to the nearest kPa value, because the ECU stores kPa; harmless.
- Without a fuel pressure sensor the pressure term is built from Base Fuel Pressure rather than measured, which
  matches the rated pressure only if the two were entered alike (`semantics-fuel.md`, Disputed).
- A fuel table "rich spot" between two breakpoints cannot be tuned out by editing the neighbours; that only mistunes
  them. Insert a breakpoint (accept the interpolate prompt so nothing changes), then trim the new row.
- At WOT an NA engine at altitude or with a restrictive intake sits below 0 kPa gauge (about 96 falling to 92 kPa
  absolute in one demo), so the ECU interpolates between the 0 and -10 kPa rows. Corrections must go to every row the
  cursor straddles (`practice` session 041).
- `vendor-doc`: with Dual Table activation set to Always ON the tables never swap. The same applies to dual ignition
  tables.
- `vendor-doc`: Ethanol status shows Error during its start-up lockout as well as on bad data, so an Error alone does
  not condemn the sensor.
- `vendor-doc`: the Continental ethanol sensor needs the internal pull-up turned on.
- `vendor-doc`: Lambda Avg is in lambda, but the AFR Average channel stays in AFR even with lambda units selected.
- `vendor-doc`: pump speed status steps in thirds only (off/33/67/100 %), so check the pressure margin at each step.
- `vendor-doc`: the help's lean example for charge temperature correction says less fuel is needed, which contradicts
  its own numbers. A lean reading needs more fuel, with the estimate moved toward IAT.
### Injector hardware by plug-in
- `vendor-doc`: on Mitsubishi, Mazda, S15, 300Z and BMW plug-ins, high impedance injectors connect directly and low
  impedance ones need ballast. Factory low impedance setups on BMW and S15 already carry ballast; leave it in. A GTS
  fitted with GT-R injectors needs ballast added, because the GTS has none. The MR2 Gen2 comes with ballast that has to
  be removed for high impedance injectors; otherwise they open slowly and the dead time is skewed.
- `vendor-doc`: on VLLink the factory 3 ohm injectors run peak-and-hold without ballast; pick replacements of 2 to 3
  ohm.
- `vendor-doc`: on the Subaru V10 adapter, big builds (about 500 hp and up) can run sequential staged injection with
  primaries on channels 1 to 4 and secondaries on 5 to 8. This costs the low-priority aux functions on those channels.
- `vendor-doc`: for staging, the Polaris RZR XP900 brings drives 3 and 4 out on its expansion connector.
- `vendor-doc`: with low impedance injectors on Xtreme, Fury or Thunder, choose Peak and Hold mode and its currents
  before the first start.
- `vendor-doc`: a saturated drive drawing over 8 A falls back to a 0.1 A hold to protect itself, so a drive that
  looks dead may have tripped because the combined impedance is too low.
- `vendor-doc`: a peak-and-hold drive trips safely at 8 A within 40 us. If peak current never arrives, it switches to
  hold after 4 ms at most; that timeout protects the drive and is not normal operation.
- `vendor-doc`: injector outputs used as aux outputs always run saturated.
- `vendor-doc`: an overheated injector tends to read lower impedance. Measure every injector on the meter's lowest
  range and subtract the lead resistance.
- `vendor-doc`: GTR fuel pump speed comes from two GP outputs whose on/off combinations give low, medium and high (for
  example, switched at injector duty near 10 % and 22 % and at 1500 / 2500 rpm). Verify at the pump: roughly battery
  voltage on high, three-quarters of it on medium and half on low.
### Tuning aids and closed loop
- `vendor-doc`: closed-loop lambda is a minor trim. A large, persistent trim means a problem in the base map.
- Training describes one symmetric closed-loop trim limit, not split by load or by rich and lean direction. The 5.6.8
  note below suggests that some builds differ (see `semantics-control.md`, Disputed).
- Mixture Map compares measured lambda with the target only and ignores the closed-loop trim active at the time.
  Either log with closed loop off, or combine the lambda error with the logged trim (for example in an external
  histogram). Set a minimum sample count (default 10) and a centre tolerance: one cell with 19 samples suggested a 26 %
  change caused by a throttle-lift transient (`practice` session 041; `practice` part 34).
- Mixture Map writes corrections only where data fell, which leaves scattered cells; blend them by hand so the table
  stays smooth.
- When the fuel and target tables use different load axes, Quick Trim needs the target load entered by hand.
- Quick Tune in automatic mode can mark a cell done before lambda settles, so the cell later sits outside the band.
  Road transients make this worse than on a dyno. One practitioner prefers manual triggering and resets cells that
  drift.
- On a V engine, if one bank's sensor jumps around (from exhaust pulsation), use the stable bank alone for Quick Tune.
- Closed-loop lambda is suspended during accel enrichment, so trim does not fight a deliberate enrichment.
- Closed-loop trim that drops to zero at high rpm is usually a lockout (rpm, MAP, TPS, coolant or rate of change).
- With nitrous active and the target unchanged, closed loop removes the fuel that the overlay added.
- `vendor-doc`: closed-loop lambda is off while launch is active (from 5.4.0), and so is knock control (from 5.1.0).
  A flat trim or no knock retard during launch is by design.
- `vendor-doc`: with dual bank closed loop, the bank trims show up in the individual cylinder fuel trims; read them as
  closed-loop action, not as user trims.
- `vendor-doc`: a target overlay meant to richen open loop also shifts the closed-loop target, so the trim will chase
  it.
- `vendor-doc`: maths on a block of cells clamps the results to the field limits without warning (from about
  5.x.x.2364/3229). After a big percentage change, look for cells pinned at a limit.
- `vendor-doc`: Quick Trim over a block is valid only if all selected cells share the same fuel and target values,
  because it scales by measured / target. If they differ, trim the cells one at a time.
- `vendor-doc`: the 5.6.8 release notes fix closed-loop 3D trim limits, so at least some builds have more than the
  single symmetric limit described above (see `semantics-control.md`, Disputed).
### Wideband and lambda
- `vendor-doc`: Lambda Avg is not built from two CAN lambdas when an external CAN wideband (the help's example: MoTeC
  LTCD) supplies them.
- `vendor-doc`: Link CAN-Lambda runs in user defined mode at 1 Mbit/s on channel ID 950. Modules ship as Lambda 1, so
  program the others first, one at a time, and assign Lambda 1 last. Power-cycle only the module just sent to.
- `vendor-doc`: a bus with mixed bit rates hides every device.
- `vendor-doc`: CAN-Lambda starts heating when engine speed passes 400 rpm and stops below 10 rpm. With no rpm packet
  it heats anyway after 2 s. Absolute exhaust pressure (50 to 250 kPa) can be fed in for compensation.
- `vendor-doc`: since 5.5.4 the internal wideband likewise waits for 400 rpm rather than cranking, so lambda reads
  blank at first fire.
- `vendor-doc`: on the 350Z plug-in the rear O2 heaters are not driven and the factory current-type front widebands
  cannot be read, so closed loop or logging needs an aftermarket wideband with a 0 to 5 V output.
### Cylinder mapping
- `vendor-doc`: wasted spark trims act on coil pairs only, and only the trims of cylinders in the first half of the
  firing order count. With firing order 1-3-4-2 and coils on 1-4 and 2-3, cylinder 1's trim moves 1 and 4, cylinder 3's
  moves 2 and 3, and the values for 4 and 2 are ignored.
- `vendor-doc`: with a single distributor only cylinder 1's trim acts, and it acts on all cylinders.
- `vendor-doc`: because of pin mapping, GTRLink in a JDM 300ZX must be set to firing order 1-5-3-6-2-4 although the
  engine fires 1-2-3-4-5-6. The ECU cylinder numbers used for trims, knock and EGT are therefore not the physical ones.
### GDI
- `vendor-doc`: before 5.6.1, fuel-cut limiting could leave 0.2 ms injector pulses. This is harmless on port injection
  but causes trouble on GDI.
- `vendor-doc`: until 5.6.3, locked-out secondaries in group/staged mode with a modelled equation still got a 0.2 ms
  pulse.
- `vendor-doc`: fault 118 or 119 shuts GDI pump control down if rail pressure stays under the low threshold, or over
  the target plus the high margin, for longer than the fault delay. A low fault means the pump cannot build pressure
  (lift pump, tuning or pump-cam phasing). A high fault means pressure cannot bleed down to the target.
- `vendor-doc`: demanding injector duty beyond 50 % causes misfire and a fault code.

## Disputed / conflicts

- **Fuel cell cap.** One practitioner's tune treats 150 as the traditional cell maximum; other sources speak of a 100 %
  cap on some ECUs and aim peaks well below it. Check the field range in the software version in use.
- **Warm-up zero point.** Training zeroes warm-up from about 60 C upward (`practice` 8.148, 8.152); the help says to
  zero the cells near normal operating temperature and gives no figure. The two do not contradict each other; the
  60 C figure stays attributed to training.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
