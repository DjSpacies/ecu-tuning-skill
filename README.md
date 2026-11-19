# ECU tuning skill

**Give your AI agent the knowledge and discipline of an experienced engine tuner.**

An agent skill for tuning gasoline, ethanol and methanol performance engines. Hand your agent a tune file and a
log, and it reads them the way a tuner would: it checks the log was captured well, finds what is wrong, explains why
from first principles, and proposes bounded, sourced changes for you to review and enter. It can plan road and dyno
sessions, coach you hands-free while you drive, and, with a live ECU tool, work directly against a running engine.

Works with Claude Code and any agent harness that can read a skill file (see `AGENTS.md`). Standard-library Python
only: nothing to install beyond Python 3.10. Diesel is out of scope.

## Why use it
- **It knows tuning, not just ECUs.** The knowledge base is built top-down: physics and combustion first (VE, charge
  cooling, knock, MBT, injector flow), then brand-neutral tuning methodology (50+ procedures, from first start to full
  load), then each ECU's own settings, quirks and traps. Advice explains *why*, not only *what*.
- **It does the number crunching.** Log analysis tools compute fuel trims, VE corrections, knock events, boost
  error, injector duty and protection coverage straight from your files, with data-quality gates that reject
  cold, transient or sparse data before any change is suggested.
- **It is safe by design.** Every change is step-limited, risk-increasing changes (leaner, more timing, more boost)
  face a higher evidence bar, and any change whose safety-critical input is unknown is withheld. It never advises
  disabling a protection. "Not enough data to change this safely" is an answer it will give.
- **It is honest about evidence.** Every finding is marked measured, inferred, assumed or asked; knowledge entries
  are tiered by source; conflicts between sources are recorded, not hidden.
- **It remembers your car.** Each vehicle gets a project folder with its profile, tunes, logs and a running history,
  so the next session picks up where the last one stopped.

## What it can do
| Ask | What you get |
|---|---|
| "How should I record a log for fuel tuning?" | A capture plan: channels, sample rate, conditions, what to avoid |
| "Is this log any good?" | Health check: missing channels, sample rate and gaps, implausible or dead sensors |
| "Why does it hesitate at 3000 rpm?" | Diagnostics scan: likely causes ranked, with the evidence for each |
| "Fix my fuel table" | Lambda error by cell, a proposed VE correction within step limits, as a diff |
| "Is it knocking?" | Knock and ignition review: where knock happens, and risk-reducing timing changes |
| "Why is boost overshooting?" | Boost control review: target vs actual, wastegate duty, control behaviour |
| "Are my protections set up?" | Protection review against your fuel, aspiration and hardware |
| "What changed between these two tunes?" | Cell-by-cell tune diff, recorded in the project history |
| "Plan my dyno day" | Ordered run cards: safest first, each with its purpose and abort conditions |
| "Tune it live" | Guided live session through an ECU tool, with backup, step limits and rollback |

Plus 50+ engineering calculators (air density, injector sizing, pulse width, ethanol blends, compressor outlet
temperature, power correction and more): `python3 -I principles/calculators/cli.py list`.

### Operating modes
- **Offline** (default): tune and log in, findings and a proposed diff out. Nothing touches the ECU.
- **Road**: run cards for the driver, two-person or solo, including a hands-free voice protocol that stays silent
  mid-pull except for safety calls.
- **Dyno**: structured procedures, correction factors and run plans.
- **Live**: reads and bounded writes through an ECU tool that implements the skill's MCP interface.

## Supported ECUs
| Platform | Support |
|---|---|
| Link G4+ | Logs (.llg) and tunes (.pclr) read; deep settings and quirks knowledge; **live tuning** with [link-g4plus-mcp](https://github.com/DjSpacies/link-g4plus-mcp) |
| Haltech | CSV logs read; settings and quirks knowledge |
| Speeduino, rusEFI, MegaSquirt | TunerStudio .msq tunes read |
| AEM Infinity, ECUMaster, FuelTech, Holley EFI, MaxxECU, MoTeC, reflash tools | Knowledge only |

Applications covered: naturally aspirated, turbocharged, supercharged, individual throttle bodies, direct injection,
E85 and flex fuel, methanol.

## Quick start
1. **Install the skill** (Claude Code):

       git clone https://github.com/DjSpacies/ecu-tuning-skill.git ~/.claude/skills/ecu-tuning

   Other harnesses: point the agent at `SKILL.md`.

2. **Create a project for your car**, outside the skill folder, and drop in your files:

       python3 -I ~/.claude/skills/ecu-tuning/tools/project/new_project.py ~/tuning-projects/my-car --platform link-g4plus
       cp my-tune.pclr ~/tuning-projects/my-car/tunes/2026-11-11_current.pclr
       cp my-log.llg   ~/tuning-projects/my-car/logs/

   For Link .pclr files, point the skill at your own PCLink install: `export PCLINK_EXE=/path/to/PCLink.exe`.

3. **Start your agent in the project and ask**:

       cd ~/tuning-projects/my-car && claude

   > Use the ecu-tuning skill. Review this log and tune.

   The agent reads the files, fills in what it can about your engine, then asks one short batch of questions
   (fuel, injectors, knock sensing, boost ceiling). "I don't know" is always a valid answer; it just makes the
   agent more conservative.

More detail, including other platforms and updating: [docs/SETUP.md](docs/SETUP.md).

## What it will not do
- Write tune files. Offline output is a proposal and a diff for a person to enter and check.
- Recommend a change when a safety-critical input (fuel, knock detection, boost ceiling, fuel system capacity,
  wideband validity) is unknown.
- Advise disabling a protection, or make live changes while the car is moving.

The skill gives engineering advice; you remain responsible for your engine and for driving legally and safely.

## Learn more
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): layers, repo layout, data flow
- [docs/OPERATING-MODES.md](docs/OPERATING-MODES.md): offline, road (with voice), dyno, live
- [docs/SAFETY.md](docs/SAFETY.md): safety model and hard rules
- [docs/SETUP-PROFILE.md](docs/SETUP-PROFILE.md): how the agent learns about your engine
- [docs/SOURCE-POLICY.md](docs/SOURCE-POLICY.md): source tiers and conflict handling
- [docs/KB-ENTRY-SCHEMA.md](docs/KB-ENTRY-SCHEMA.md): format of every knowledge entry
- [docs/MCP-INTERFACE.md](docs/MCP-INTERFACE.md): live ECU tool interface, for integrators
- [docs/PLATFORM-ADAPTERS.md](docs/PLATFORM-ADAPTERS.md): adding an ECU

Contributions welcome: [CONTRIBUTING.md](CONTRIBUTING.md).
