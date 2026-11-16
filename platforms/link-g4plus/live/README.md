# Live connection (moved)

The live Link G4+ tooling (direct serial client, live read and tuning tools, MCP server) is its own project:
[github.com/DjSpacies/link-g4plus-mcp](https://github.com/DjSpacies/link-g4plus-mcp). Its `.live.json` logs load
through this platform's adapter (`../parser/adapter.py`), so every analysis in this skill runs on them.
