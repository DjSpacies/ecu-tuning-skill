---
id: platforms/maxxecu/quirks
title: MaxxECU quirks
layer: L3
confidence: low
sources: [practice]
verified: 2026-11-11
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/maxxecu/semantics]
supersedes: []
---

# MaxxECU quirks

How MaxxECU and MTune behaved in training material, mainly on a Honda B18C competition car (no idle air valve, pump
fuel, distributor ignition) and with the PDM20. What settings mean is in `semantics.md`. Tags `practice` and
`practice` mark the training source.

## Claim

On MaxxECU, the rev limit number marks the start of the cut ramp, so the engine passes it; the VE table holds true VE
only with lambda multiplication enabled; idle ignition control is gated by activation limits that can silently
disable it (a MAP limit of zero did); the internal wideband's heater mode decides whether there is lambda data at
first start; the cell autotune key rarely lands on target in one press; and the built-in scope is the tool for VR
edge choice, which on a Honda distributor was opposite for crank and cam.

## Why (derivation)

- A soft cut with a control range ramps cut from 0 % at the entered limit to 100 % one range above. Peak rpm is
  therefore the limit plus up to the range.
- Without the lambda term in the fuel equation, the table must also carry the mixture, so its values are VE divided by
  target rather than VE.
- Activation limits are logical ANDs. Any one at an impossible value (MAP at 0 kPa) keeps the function off with no
  other symptom.
- Autotune applies the measured over target ratio to one cell. If the operating point is between cells, interpolation
  spreads the change, and residual configuration or injector errors remain.

## Assumptions

- MTune of the period shown; Honda B18C on a distributor with VR crank and cam signals.
- Default activation limits as found on that base map.

## Breaks when

- Later MTune versions may change limit semantics or autotune behaviour.
- Coil-on-plug installations do not share the distributor discharge-time concerns.
- Records from one car and one practitioner; treat numbers as examples.

## Practical use

### Limits and protection
- With the limit at 8800 rpm and a 200 rpm range, cut ramps from 0 % at 8800 to 100 % at 9000, so the engine goes
  past 8800. If 8800 is the true maximum, enter 8600 with a 200 rpm range. A zero range is a hard instant cut, harsh
  on engine and driveline (`practice` 350).
- MAP sensor failure: flag outside about 0.1 to 4.9 V and substitute a limp value around 60 to 70 kPa, which is never
  right but may get the car home (one practitioner's view, `practice` 8.168).
- A single momentary button can start and kill the engine using a logic output: button pressed AND rpm above about
  600, held about 2 s, drives the stop-engine function (`practice` 319).
- The PDM20 example ran the fan on at 88 C with 2 C hysteresis and disabled it above 100 km/h, where ram air
  suffices (`practice` 319).

### Fuel model
- Enable the option that multiplies by lambda target if the VE table is to hold true VE; without it the table absorbs
  the mixture target (`practice` 8.168).
- Displacement feeds the airflow calculation; confirm real capacity on overbored or stroked engines (`practice`
  8.168).
- Fuel pressure compensation modes: manifold-referenced (return system with a MAP-referenced regulator, as on the
  factory B18C), fixed (returnless or unreferenced) and sensor tracking where a sensor is fitted (`practice`
  8.168).
- The crank-to-run threshold defaults to 300 rpm; check actual cranking speed before relying on it (`practice`
  8.168).
- The cell autotune key often does not land on target in one press, and gives poor results at idle sitting between
  two cells. Centre the operating point, press it a couple of times, finish by hand (`practice` 318).
- Initial sequential injection timing in the course was a single end-of-injection value of 400 degrees BTDC
  (`practice` 8.168).

### Ignition and trigger
- Ignition system delay (about 80 microseconds typical) is an rpm-dependent timing error, checked with the engine
  running (`practice` 8.168).
- Dwell has a minimum discharge time for distributor setups at high rpm: 1 ms used, with the manufacturer advising
  not below 0.5 ms (`practice` 8.168).
- VR inputs trigger at the zero crossing after the arming threshold, from an rpm table (default about 1.5 V at
  1600 rpm rising to 5 V above 4000) (`practice` 8.169).
- The built-in scope marks the trigger event on a cranking capture. On the Honda distributor the crank signal suited
  a falling edge but the cam (home) signal dipped below zero before rising, so it needed a rising edge, opposite to
  convention. The wrong VR edge shows as timing drift with rpm; irregular cranking waveforms from compression are
  normal (`practice` 8.169).

### Idle without an idle valve
- The B18C race car had no idle air valve, so idle was held with the throttle stop and ignition. Idle ignition
  control uses a table of timing against rpm error from target; its activation limits (maximum TPS about 0.4 %,
  maximum rpm about 1500 to 1600, maximum MAP) must all pass. A maximum MAP of zero was silently disabling it until
  raised to 35 kPa with idle at about 28 kPa (`practice` 8.167, 8.173).

### VTEC
- Switched on rpm alone (3500 rpm, 50 rpm hysteresis on the race car), VE rose across the changeover at WOT but
  dropped across it at part load: the high cam helps only at high load near the switch. Factory Honda windows the
  changeover by rpm and MAP (`practice` 318).
- MaxxECU can select separate low-cam and high-cam fuel and ignition tables through a 4D axis on cam state scaled
  0/1. This avoids a diagonal boundary in one table and keeps VE right even when VTEC is inhibited (stationary, cold
  oil). Expect about twice the tuning work; rpm-only switching with one table suits a simple job (`practice`
  8.170).

### Internal wideband
- Select LSU 4.9 or 4.2 before first plugging the sensor in; some ECUs default to 4.2 and the wrong type can damage
  the sensor (`practice` 8.168, `practice` 318).
- Heater on engine start protects the sensor but leaves no lambda for about 30 to 40 s after start, exactly when
  cranking and warm-up enrichment are judged. The course switched to heat at ECU power-up for first start and cold
  start work, then back (`practice` 8.168, 8.172).

### Logging
- In MTune, set the lambda log axis manually (about 0.7 to 1.2) rather than auto-range, which spreads the scale so far
  that small errors vanish; the log cursor marks the corresponding cell in the VE or ignition table (one practitioner's
  preference, `practice` 8.176).

## Worked example

Illustrative, built on the session's settings. B18C race car, limiter wanted at a true 8800 rpm. The tune shows
limit 8800, range 200; a log shows peak rpm on the limiter well above 8800. Reading: the ramp ends at 9000, so the engine is behaving as configured. Enter 8600 with range
200 and peak rpm should not pass 8800. Separately, the log shows idle ignition correction stuck at 0 while idle rpm
wanders and MAP is 28 kPa: the idle ignition MAP activation limit is 0 kPa. Raising it to 35 kPa activates control.

## Disputed / conflicts

- **Where the limit sits in the ramp.** On MaxxECU the entered value is the start of the cut; on other ECUs it may be
  the end (the session's own caveat). Read the product's help or log peak rpm on the limiter before trusting a
  number.
- **Wideband heater at power-up.** It gives first-start data but shortens sensor life from condensation shock. The
  course uses it only temporarily.

## Citations

- practice: Practitioner training and tuning practice, distilled and cross-checked.
