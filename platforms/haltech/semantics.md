---
id: platforms/haltech/semantics
title: How Haltech fuel tables behave
layer: L3
confidence: medium
sources: [vendor-documentation, practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: []
supersedes: []
---

# How Haltech fuel tables behave

Tags: `vendor-doc` (Elite Series help, ESP 2.59.3, and the Haltech knowledge base) and the training source ids
`practice`, `practice`, `practice` for how tuners read and use these settings on Platinum Pro, Elite (ESP
software) and Elite/Nexus (NSP software) units. What the settings mean is here; how the product really behaves, its
traps and workarounds are in `quirks.md`.

## Claim

On a Haltech the meaning of most fuel numbers is set by a few configuration choices: the Tuning Method (VE, Mass Air
Flow or Injection Time), whether automatic air-temperature compensation is on, and whether a correction acts on fuel
(to hold the target) or on the lambda target (to change it). An agent must read those choices before interpreting any
Fuel Base value, correction table or proposed percentage change. Idle, transient, closed-loop, knock and limiter
strategies are likewise built from a base (feed-forward) table plus correctors whose units depend on configuration.

## Why (derivation)

### Fuel model
- `vendor-doc`: the Tuning Method decides what Fuel Base means and must be chosen before tuning: Volumetric Efficiency
  (values describe engine filling; the Target Lambda table feeds the final calculation), Mass Air Flow (values are a
  multiplier on the sensor curve, starting at 1.000) or Injection Time (values are time).
- In VE mode the ECU computes air mass from displacement, VE, measured MAP and charge temperature (ideal gas), then fuel
  mass from the lambda target and fuel stoichiometry, then pulse width from injector flow at the actual differential
  pressure plus dead time. Every setup number (capacity, cylinder count, injector flow and rated pressure, fuel type
  and density, fuel pressure reference and base pressure) is therefore part of the equation. If any is wrong, the
  error is absorbed into the VE table and its numbers stop meaning true VE (`practice` Practical Standalone Tuning
  8.60, 8.72; `practice` 165).
- Fuel pressure reference: constant for a returnless fixed-pressure system, MAP-referenced for a return system with a
  manifold-referenced regulator. The ECU uses it with MAP to compute differential pressure across the injector, which
  indexes flow and dead time. The training sessions enter a measured base pressure (around 380 kPa on a returnless
  VQ35 car) rather than a nominal one.
- Fuel Type can be Petrol, Ethanol, Ethanol Petrol Blend, Flex Fuel or Methanol (`vendor-doc`); the NSP help gives a
  petrol density default near 737 kg/m3, used by the VE model.
- In VE mode MAP stays a multiplier even when the VE table is on a TPS axis (alpha-N). Doubling absolute manifold
  pressure doubles computed air and fuel, so lambda holds. The usual layout on multi-throttle turbo engines is VE on
  TPS, ignition on MAP, lambda target on MAP (`practice` 089).
- Engine pressure ratio (intake over exhaust manifold pressure) can be used as fuel load on the Elite; it accounts for
  exhaust-side pressure, so altitude and backpressure are compensated without a tuned baro table, at the cost of an
  exhaust pressure sensor and a less intuitive load number (`practice` 241, 245).

### Air temperature and charge temperature
- `vendor-doc`: with Auto V.E. Air Temp Compensation on, the air temperature table becomes a correction to the
  automatic gas-law calculation; it should start at zero.
- NSP has a coolant temperature bias table (rpm by load) that blends IAT and coolant temperature into an estimated
  charge temperature. At low airflow (idle, cruise, high vacuum) the air has time to pick up heat from manifold and
  ports, so the default leans toward coolant (in the course example roughly 60-75 % coolant at low rpm and high
  vacuum, falling to a few percent at high rpm and load). The course advises leaving the default unless the tuner is
  advanced, since it is hard to calibrate (`practice` 8.60).
- Baro: full baro correction is not automatic; the baro correction table must be enabled and tuned whether load is TPS
  or MAP (`practice` 241).

### Fuel corrections versus lambda-target corrections (VE mode)
- A fuel correction (IAT fuel, coolant fuel, warm-up) exists to make the engine reach the current target as conditions
  change. A lambda-target correction changes the target itself (for example a little richer at low coolant temperature,
  or richer at high IAT on a turbo engine for knock margin) (`practice` 074, 165, 205).
- The distinction matters because closed loop drives to the target: richness put into a fuel correction survives only
  until closed loop engages, then the trim removes it. Richness put into the target survives closed loop.
- In Injection Time mode the target table does not change fuel delivered, so a deliberate richening at high IAT is made
  by making the IAT fuel correction less negative there instead (`practice` 074).

### Idle control
- The base idle table is a percentage of the actuator's range: of the configured maximum DBW idle position for
  drive-by-wire, of duty for a solenoid valve, of the configured step range for a stepper. The tuning method is the same
  whatever the hardware (`practice` 117).
- Target idle is a table on coolant temperature, optionally with vehicle speed and A/C axes. Closed-loop idle adds a
  PID correction to the base opening, and an idle ignition correction adds or removes timing according to rpm error.
  An rpm-error axis works at whatever target coolant temperature sets; an absolute-rpm axis only suits one idle speed
  (`practice` 207; `practice` 8.77).
- Time-based post-start offsets exist for both idle target and base opening, a decel offset with decay time catches
  return-to-idle, and generic idle-up offsets can be triggered by inputs such as power steering or drive engaged.
- Idle long-term trim learns the average closed-loop correction and can be applied back into the base table.

### Transient fuel
- Elite (ESP): enrich rate is a table of current TPS by TPS rate, multiplied by an enrich amount table by rpm. More is
  needed from near-closed throttle and for faster movement. The amount number is a pseudo-VE term that scales with
  assumed VE, which is why its default rises with rpm. The parameter labelled load acceleration deadband (%/s/s) acts
  as the decay rate: smaller keeps enrichment longer. Detect duration is a filter time the rate must persist before
  enrichment starts (`practice` 233).
- Platinum Pro: an ms table (rpm by starting TPS) scaled by a percentage table on TPS change per 10 ms; part can be
  delivered asynchronously (extra pulses outside the schedule) through an async percentage table with a lockout delay
  (`practice` 048).
- NSP: a predicted MAP table (TPS by rpm) stands in for the lagging MAP sensor for a predicted MAP time after a throttle
  event, with transient TPS scaling as the sensitivity, plus a fuel film model (film percentage by coolant and MAP,
  evaporation time constant) (`practice` 348).
- Synchronous enrichment lengthens scheduled pulses; asynchronous adds pulses. Async matters at low rpm and where the
  injector is far from the valve (rotaries, injectors high in the runner).

### Closed loop and learning
- Short-term trim corrects continuously; long-term trim stores persistent short-term correction per cell into a saved
  table so short-term returns toward zero. One practitioner's view is that this per-cell storage works better than
  factory long-term trims that learn over a few broad zones (`practice` altitude session).
- Parameters: trim authority limits, minimum coolant temperature, lockouts during post-start and coolant correction,
  optional rpm/TPS/MAP windows, a long-term gain, and a rich bias (0-10 %) that makes the learned table sit richer than
  target so short-term trim pulls fuel. The NSP delay table by rpm is a re-engagement delay after events such as
  overrun cut, not a transport-delay compensation (`practice` 063, 358).
- Dual-bank: when bank long-term trims are applied, the ECU moves their average into the base table and leaves each
  bank with half the difference, so the bank split is kept (`practice` 063).
- With CAN widebands the Elite allows closed loop throughout the map including full load, unlike factory strategies
  that restrict it to idle and cruise (`practice` 054).

### Knock
- Knock threshold is a table on rpm; centre frequency is set per engine. Short-term knock control retards and recovers.
  Long-term knock trim stores a fixed retard per knock event per cell (the session shows 0.5 degree per event up to a
  configurable maximum) and can be applied to the base ignition table (`practice` 057, 063).
- `vendor-doc`: knock frequency should be where the signal differs most between no-knock and knock.

### Limiters, protection and launch
- NSP limiter cut types: hard cut (all cylinders cut at end rpm, restored below end rpm minus hysteresis), cut-off mode
  (cut ramps from 0 % at end rpm minus a range, default 500 rpm, to 100 % at end rpm, with an adder 0-255 that acts as a
  randomiser), and combined modes in which the second cut method is added 100 rpm above the end rpm
  (`practice` 374).
- Tables on coolant temperature interpolate between breakpoints, so a coolant-based rev limit falls gradually unless two
  breakpoints are placed about 1 degree apart to make a step (`practice` 253).
- Engine protection uses severity levels; each sensor fault or out-of-range condition is assigned a level, and each
  level has its own response (target enrichment, boost reduction, retard, rpm limit, DBW throttle limit)
  (`practice` 253, 372).
- Platinum launch: the launch ignition table is an absolute timing map, not an offset; anti-lag launch is the stationary
  launch limiter with retard, anti-lag rally is the off-throttle boost-holding system (`practice` Platinum Pro
  launch session).
- `vendor-doc`: torque management never advances timing past the base ignition table.

### Injector model
- Elite offers a simple model (flow, reference pressure, dead time) and a full characterisation (dead time by
  differential pressure and battery voltage, flow by differential pressure, short pulse adder). The dead time table
  against both pressure and voltage lets the ECU re-look-up latency at once when a fuel pressure sensor sees pressure
  change (`practice` 8.72; `practice` 054, 407; `practice`).
- Under Injection Time the table value excludes dead time; the delivered pulse is table value plus dead time.

### Other settings
- `vendor-doc`: long-term fuel trim corrections are applied to two tables and one base table in a specific way.
- Trigger options: a number of teeth before a sync attempt (helps engines with uneven cranking speed), quick start
  (batch or wasted spark while cranking on sequential setups), filters (start at zero), and whether the home signal is
  used always or only until first sync (`practice` 8.61).
- The TDC angle relates displayed timing to crank position; base maps supply one but it must still be confirmed with a
  timing light (`practice` 8.61, 8.75).
- Platinum cam control drives the cam to its stop during cranking and records that position as zero automatically;
  outputs have duty clamps, a dead band and a coolant lockout (`practice` Platinum cam session).
- Platinum MAF mode: the main table is a correction multiplier on a pulse width calculated from MAF and injector data
  (`practice` MAF/ms/VE session).

## Assumptions

- Elite on ESP 2.59.3 for `vendor-doc` facts. Training observations span Platinum Pro, Elite on ESP and Elite/Nexus on
  NSP; parameter names and defaults differ between ESP and NSP and between firmware versions.
- Default settings as shipped; a vendor base map may differ.

## Breaks when

- Platinum, Elite and Nexus generations do not share every strategy (transient fuel in particular is structured
  differently in each); check which software the file came from.
- Defaults and numbers quoted from the training sessions are examples on specific cars, not product limits.
- A file whose Tuning Method was changed after tuning holds values whose meaning has changed.

## Practical use

- Before proposing any fuel change, record Tuning Method, auto air-temperature compensation state, fuel pressure
  reference and base pressure, and whether closed loop and long-term trims are on.
- A percentage change applies directly in VE mode. Under Injection Time it is the same relative change, but under Mass
  Air Flow it is a change to a multiplier: state which method is active.
- To make a VE-mode engine richer in some condition, change the lambda target or its correction; to make it reach the
  target it misses, change VE or a fuel correction.
- With auto air-temperature compensation on, the manual IAT fuel table should start at zero and carry only small
  residual corrections; a populated table means double correction (see `quirks.md`).
- Read idle base values as percent of the configured range; when the maximum DBW idle position or throttle body
  changes, rescale the base table in proportion.
- `vendor-doc` guidance carried forward: tune rich, then lean out slowly; keep sustained high load and speed short to
  limit heat. Average the MAP signal across one full cylinder period or longer. VE tuning needs correct capacity,
  injector flow and target table. If VE numbers look strange, correct dead time, but do not assume every rough idle is
  a dead-time fault; the short pulse adder final cell should be 0 ms. Boost control: start duty close to target so
  boost comes in just under it; raise derivative slowly. A vehicle speed sensor is highly recommended with idle control.
  The timing light should be a simple fixed unit. Mount a MAP sensor above injector level so fuel cannot run into it.
- Datalogging can run to internal memory, conditionally on a channel or switch, or to a laptop (`vendor-doc`).

## Worked example

VE mode, auto air-temperature compensation on, closed loop on. A turbo engine should run lambda 0.86 above 60 C IAT
instead of the 0.88 base target. Wrong: add 2 % fuel in the IAT fuel table at 60 C. That double-corrects on top of the
gas-law correction, and once closed loop is active the trim pulls the 2 % back out toward 0.88. Right: add an IAT
correction of -0.02 to the lambda target at 60 C. The fuel model then delivers the extra fuel and closed loop holds
0.86. Had the same file been in Injection Time mode, the target would not affect fuel; the session's equivalent was
to make the IAT fuel correction about 2 % less negative at 60 C (for example -8 % instead of -10 %) (`practice` 074).

## Disputed / conflicts

- Warm-up enrichment: Haltech material suggests doing warm-up in the post-start correction (coolant by run time). One
  practitioner in the training sessions disagrees because that table has no load axis; he uses the 3D coolant correction for equilibrium
  warm-up and post-start only to bridge the first seconds and hot restarts (`practice` 390). Test: tune both ways
  on a cold start and compare lambda error across load once post-start has decayed.
- Auto air-temperature compensation: the course treats it as the normal choice with a zeroed manual table; one
  presenter often turns it off and hand-tunes a manual IAT table because the model over-corrects, mainly at idle under
  heat soak (`practice` 054, 071). Test: log lambda error against IAT during heat soak with the model on.
- Fuel mode: presenters prefer VE mode for unfamiliar engines and see little reason for MAF mode on an aftermarket ECU
  unless a race rule requires it (`practice` 054, 071); this is preference, not a product rule.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
