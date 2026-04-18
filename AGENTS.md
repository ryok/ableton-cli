# AGENTS.md

## Project Overview

ableton-cli is a CLI tool that controls Ableton Live via TCP socket connection to the [AbletonMCP Remote Script](https://github.com/ahujasid/ableton-mcp). Originally ported from an MCP server implementation to a standalone CLI using Click.

## Architecture

```
ableton-cli (this project)          Ableton Live
┌──────────────────────┐            ┌──────────────────────────┐
│  ableton_cli/main.py │──TCP/JSON──│  AbletonMCP Remote Script│
│  (Click CLI)         │  :9877     │  (Socket Server)         │
│                      │            │                          │
│  ableton_cli/        │            │  Runs inside Ableton as  │
│  connection.py       │            │  a Control Surface       │
│  (Socket Client)     │            │                          │
└──────────────────────┘            └──────────────────────────┘
```

- **`connection.py`** – `AbletonConnection` class handling TCP socket communication. Sends JSON commands, receives JSON responses. Manages connection lifecycle and chunked response assembly.
- **`main.py`** – Click CLI definition. All commands are thin wrappers that call `connection.send_command()` with the appropriate command type and params.

## Communication Protocol

Commands are JSON objects sent over TCP to `localhost:9877`:
```json
{"type": "command_name", "params": {"key": "value"}}
```

Responses:
```json
{"status": "success", "result": {...}}
{"status": "error", "message": "..."}
```

State-modifying commands (create_midi_track, set_tempo, etc.) include 100ms delays before and after to give Ableton time to process.

## Development

```bash
uv venv && uv pip install -e .
source .venv/bin/activate
ableton --help
```

## Key Conventions

- Python 3.10+, type hints throughout
- Click for CLI framework – subcommand groups: `track`, `clip`, `browser`
- No external dependencies beyond `click`
- Entry point: `ableton_cli.main:cli`
- JSON output for info commands (`session`, `track info`, `browser items`)
- Human-readable confirmation messages for mutation commands

## Adding a New Command

1. If it's a new command type, no changes needed in `connection.py` – just call `send_command("new_type", params)`.
2. Add the Click command in `main.py` under the appropriate group (`@cli.command()`, `@track.command()`, `@clip.command()`, or `@browser.command()`).
3. Follow the existing pattern: get connection via `_get_conn(ctx)`, call `send_command`, output result.
4. The corresponding handler must exist in the Ableton Remote Script (`AbletonMCP_Remote_Script/__init__.py`).

## Testing

Requires Ableton Live running with the AbletonMCP Remote Script loaded. No automated test suite yet – test manually against a live Ableton session.
