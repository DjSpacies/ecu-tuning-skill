# Find the likely cause of a symptom before tuning it

## Inputs
- Required: log. Safety critical: none (this workflow only reports).
- Useful: tune (adds the table checks: axis coverage, rows used at full throttle, ignition shape).
- Irrelevant: everything else; do not ask for it.

## Load only
- methodology/data-quality and methodology/log-capture-protocol
- tools/analysis/diagnostics.py, only the test a finding names in its `diagnostic` field
- the KB entry a finding points to, when the user wants the reasoning
- the platform's semantics.md and quirks.md

## Steps
1. Run the log health check first. Do not diagnose a log that fails it.
2. Run `python3 -I tools/analysis/run.py diagnostics-scan --platform <ecu> --log LOG [--tune TUNE] [--profile P.json]`.
3. Report faults first, then warnings, grouped by what they block:
   - Sensor and trigger faults (MAP against baro, temperature agreement, throttle end points, rpm spikes, flex sensor): fix before any tuning.
   - Fuel supply (differential fuel pressure, injector saturation, lean with duty headroom): fix before fuel table work. A table edit cannot fix supply.
   - Closed-loop effects (trim at its clamp, trim masking base error): the fuel analysis cannot see these errors from lambda alone. Ask for a log with closed loop off.
   - Compensations (air and coolant temperature slopes): fix the compensation before editing cells.
   - Knock (noise floor against load, repeatable against one-off events): say what is unconfirmed and what data would settle it. Never treat noise-floor or unmeasured bands as safe for more advance.
   - Lean events by cause: cut, overrun and transient events are not mixture errors. Report sustained lean under load as a stop condition.
   - Oil pressure: a sustained drop is a stop condition whatever the cause.
4. List the tests in the "Not checked" note with what each needs, so the next log can supply it (workflows/log-capture).
5. Report with the evidence ledger. Diagnostics never propose table changes; changes go through the fuel or ignition workflow afterwards.

## Refuse when
Never refuse to report. Do not turn a diagnostic into a table change, and do not call an unchecked test a pass.
