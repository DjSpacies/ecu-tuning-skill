# Link G4+

Family: Link G4+ (PCLink 5.6.x). Reads tunes (.pclr or decoded XML) and ECU logs (.llg). Does not write tunes.
Facts are tagged by evidence: `vendor-doc`, `re-derived` (from file-format analysis) or `sample-observed`.

| File | Holds |
|---|---|
| `formats.md` | File formats |
| `channels.yaml` | Native log channel to canonical channel |
| `tables.yaml` | Native table to role |
| `semantics.md`, `quirks.md`, `inference.md` | Behaviour, gotchas, what files reveal |
| `g4x-g5-notes.md` | Differences in the G4X and G5 generations |
| `parser/` | `llg.py`, `pclr.py`, `adapter.py` |
| `mcp-map.yaml` | Mapping for a live ECU tool |
| `live/` | Pointer to [link-g4plus-mcp](https://github.com/DjSpacies/link-g4plus-mcp), the live connection and MCP server; its `.live.json` logs load through `parser/adapter.py` |
| `terms.yaml` | Vocabulary |
