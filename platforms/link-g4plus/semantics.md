---
id: platforms/link-g4plus/semantics
title: How Link G4+ tables behave
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-17
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: []
supersedes: []
---

# How Link G4+ tables behave

Facts tagged `vendor-doc` come from the PCLink G4+ 5.6.8 help and apply to that version; the help outranks training
material on what a setting does. Points tagged `practice`, `practice` or `practice` come from training
sessions recorded on G4+ (and ViPEC, its twin of that era) and describe how tuners read and use the settings. Behaviour
that surprises people, and workarounds, are in `quirks.md`. G4X and G5 run PCLink 7.8.2 with different ids and some
different behaviour (`g4x-g5-notes.md`); nothing here carries over to them unchecked.

## Claim

A G4+ number only has meaning together with the mode that consumes it. In Traditional fuel mode a fuel cell is a
percentage of Master Fuel, scaled in the background by MAP (when Load = MAP) and by stoich/target (when the lambda
target is in the equation); in the Modelled modes it is an efficiency that the ECU turns into fuel mass from engine
capacity, injector data, fuel properties and charge temperature. Limit tables mark the end, not the start, of a cut
range; idle ignition tables are indexed by rpm error; closed-loop boost and idle run in stages with lockouts. Reading a
tune or a log correctly means resolving each of these before comparing a number with anything else.

## Assumptions

- PCLink G4+ 5.6.x firmware and help; Modelled modes need firmware 5.2.0 or later. Training sessions were recorded on
  various G4+ and ViPEC firmware of that era; where they disagree with the help, the help governs what a setting does.
- Spark-ignition engines on gasoline, ethanol blends or methanol.
- Training numbers are what one practitioner used on one engine, not limits or defaults to copy.

## Breaks when

- A tune from another generation (G4, G4X, G5) or a firmware outside 5.6.5 to 5.6.8: ids and behaviours can differ
  (see `quirks-io.md`).
- Modelled mode with poorly characterised injectors or a wrong capacity: the VE table absorbs the error and no longer
  transfers between injectors or targets (`practice` VE model session; `practice` session 089 found VE tables
  from three ECUs on one engine were not interchangeable).
- A fuel table tuned with odd target values in the equation: the table compensates and looks strange; turning the
  target function on or off after tuning shifts the whole tune.
- A turbo engine on exhaust back-pressure the model cannot see: mixture drifts rich at high boost and rpm even when
  the efficiency table is right at spring pressure (`practice` sessions 085 and 133).

## Practical use

Topic files (load only the ones a task needs):

| File | Holds |
|---|---|
| `semantics-fuel.md` | fuel, injection and lambda |
| `semantics-ignition.md` | ignition, triggers, knock and cams |
| `semantics-io.md` | inputs, outputs, logging and CAN |
| `semantics-control.md` | limits, boost, idle, throttle and launch |

## Worked example

See `semantics-fuel.md`.

## Disputed / conflicts

Topic-specific disputes are in each topic file.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
