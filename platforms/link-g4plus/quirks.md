---
id: platforms/link-g4plus/quirks
title: Link G4+ quirks
layer: L3
confidence: medium
sources: [vendor-documentation, file-format-analysis, practice]
verified: 2026-11-17
applies_to: {fuels: [gasoline, ethanol, methanol], engines: [all]}
depends_on: [platforms/link-g4plus/semantics]
supersedes: []
---

# Link G4+ quirks

Tags: `vendor-doc` (PCLink G4+ 5.6.8 help), `re-derived` (reverse-engineering notes), `sample-observed` (vendor
sample tunes and logs), and the training source ids `practice`, `practice`, `practice` for behaviour seen
by tuners on real cars (G4+ and ViPEC of that era). What settings mean is in `semantics.md`; this file is about how the
product actually behaves and the traps it sets. Everything here is G4+ (help version 5.6.8); G4X and G5 run PCLink
7.8.2 and are covered in `g4x-g5-notes.md`.

## Claim

Most G4+ surprises come from a small set of behaviours: limits that start cutting before the number entered; the
lowest of several active limits silently winning; newly enabled or re-dimensioned tables holding junk or losing
values; tuning aids that compare measured lambda with target while ignoring other active corrections; edits that are
lost unless stored; and channels whose meaning depends on configuration (gauge versus absolute pressure, knock gain,
closed-loop trim). A further group changed between 5.x firmware releases, so the firmware a log came from is part of
reading it. An agent reading a G4+ tune or log should test for these before diagnosing the engine.

## Why (derivation)

- Limits are proportional controllers: cut rises across a control range that ends at the table value, so cutting
  begins one range below it (`semantics-control.md`, Limits). With several limits active the ECU takes the minimum, so a
  forgotten table whose safe value equals today's rev limit caps tomorrow's.
- Tables are allocated from memory slots. Enabling a new table, or switching a 2D table to 3D, does not initialise the
  contents to anything meaningful.
- Mixture Map and Quick Tune work from measured minus target lambda. Any other fuel change that was active at the time
  (closed-loop trim, warm-up, accel enrichment) is not removed from that comparison, so the suggested correction is
  biased by it.
- Closed-loop controllers in this generation act on error alone with stage switching; a controller that looks perfect
  under the steady, repeatable load of a dyno can still misbehave when load and gear change on the road.

## Assumptions

- The ECU runs G4+ firmware 5.6.x with the PCLink of that era. Training sessions were recorded on various G4+ and
  ViPEC firmware, and some behaviour (for example the boost derivative issue) may have been changed in later firmware.
- Settings are the defaults as shipped; a vendor base map may differ.

## Breaks when

- Firmware differences beyond 5.6.5 and 5.6.6, the versions in the samples, are unknown.
- G4X and G5 use different software and ids; none of these quirks carry over without checking.
- Training observations come from a handful of cars. A behaviour reported only once, from one practitioner's
  experience, may be specific to that car.

## Practical use

Topic files (load only the ones a task needs):

| File | Holds |
|---|---|
| `quirks-fuel.md` | fuel, injection and lambda |
| `quirks-ignition.md` | ignition, triggers, knock and cams |
| `quirks-io.md` | inputs, outputs, logging and CAN |
| `quirks-control.md` | limits, boost, idle, throttle and launch |

## Worked example

A log shows a VQ35 limiting at about 6500 rpm with the rev limit table at 6700, a GP oil-pressure limit with its safe
area at 6700, and a request to raise the limit to 7200 after a valve-train upgrade.
1. The 200 rpm control range explains limiting from 6500: cut starts at 6700 - 200.
2. Raising the main table to 7400 (so cutting starts at 7200) changes nothing, because the GP table's 6700 is now the
   lowest active limit.
3. Set the GP table's safe area to 10000 and its low-pressure cells to the protection value; then the main limit takes
   effect.
4. Log rpm, active limit, limiter status and percent cut on a full-throttle pull: a smooth cut trace with no spike past
   the value means the start cut is close to what the engine needs (`practice` sessions 036, 084, 171).

## Disputed / conflicts

Topic-specific disputes are in each topic file.

## Citations

- vendor-documentation: ECU and tuning-tool vendor documentation.
- file-format-analysis: Analysis of file formats from files the user owns, for interoperability.
- practice: Practitioner training and tuning practice, distilled and cross-checked.
