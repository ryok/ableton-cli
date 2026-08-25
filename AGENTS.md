# AGENTS.md

## Project Overview

ableton-cli is a CLI tool that controls Ableton Live via TCP socket connection to the bundled AbletonMCP Remote Script. The Remote Script is based on [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) with ableton-cli-specific command handlers. Originally ported from an MCP server implementation to a standalone CLI using Click.

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
5. **Register state-modifying commands in the main-thread list.** Adding an
   `elif command_type == ...` branch to the dispatch is not enough. The branch
   sits inside a block guarded by an explicit whitelist a little further up:

   ```python
   elif command_type in ["create_midi_track", "set_track_name", ...]:
   ```

   Anything not in that list is handled on the worker thread, and Live's API
   refuses state changes from there. A command left off the list looks like it
   was never added.

## Deploying a Remote Script change

The Remote Script Live runs is the *installed copy*, not the one in this repo:

```
/Applications/Ableton Live NN Suite.app/Contents/App-Resources/MIDI Remote Scripts/AbletonMCP/__init__.py
```

(The README's `~/Music/Ableton/User Library/Remote Scripts/` path is the other
supported location – check which one actually exists before editing.)

Copy the file over, delete the neighbouring `__pycache__`, then **restart Live
completely**. Toggling the Control Surface to None and back in Preferences >
Link/Tempo/MIDI is *not* sufficient: the log shows the surface being
re-registered, but Python serves the module from `sys.modules` and the old code
keeps running. The symptom is `Unknown command: <your_new_command>` from a CLI
that clearly contains it.

`main.py` turns that specific error into an explanatory message rather than a
traceback, since it is the failure every contributor hits first.

Live's log, useful for confirming what actually loaded:

```
~/Library/Preferences/Ableton/Live NN.N.N/Log.txt
```

## Live API limits worth knowing

- **Arrangement clips cannot be created from scratch or deleted.** Build a
  Session clip first and use `duplicate_clip_to_arrangement`. To replace a
  misplaced Arrangement clip, just place the correct one over the same range –
  Live overwrites the region, so no delete call is needed.
- **Mixer volume has no dB setter.** `mixer_device.volume.value` is 0-1 on a
  non-linear curve (0.85 is roughly 0 dB). `str_for_value()` reports the dB the
  user sees and the curve is monotonic, so `set_track_volume` bisects to hit an
  exact displayed value.
- **`clip add-notes` via argv overflows the shell** at a few hundred notes. Use
  `--file`.

## Project Structure

```
ableton-cli/
├── ableton_cli/              # CLI source code
│   ├── __init__.py
│   ├── connection.py         # TCP socket client
│   └── main.py               # Click CLI commands
├── remote_scripts/           # Bundled Ableton Remote Script
│   ├── README.md             # Upstream base and local changes
│   └── AbletonMCP_Remote_Script/
│       └── __init__.py       # Control Surface socket server
├── skills/                   # AI agent skills (visible to repo visitors)
│   ├── README.md             # Skill installation guide
│   └── ableton-live/
│       └── SKILL.md          # Claude Code skill definition
├── .claude/
│   └── skills/
│       └── ableton-live/
│           └── SKILL.md → ../../../skills/ableton-live/SKILL.md
├── AGENTS.md                 # This file
├── CLAUDE.md → AGENTS.md
├── README.md                 # English docs
├── README.ja.md              # Japanese docs
└── pyproject.toml
```

## Testing

Requires Ableton Live running with the bundled AbletonMCP Remote Script loaded. No automated test suite yet – test manually against a live Ableton session.
