# ableton-cli

A CLI tool to control Ableton Live from your terminal. Communicates with the bundled AbletonMCP Remote Script over TCP sockets.

[日本語版 README](README.ja.md)

## Why CLI over MCP?

ableton-cli uses a bundled Remote Script based on [Ableton MCP](https://github.com/ahujasid/ableton-mcp), with CLI-specific command handlers. The runtime shape is still the same: AI agents issue commands through the CLI, and the CLI talks to Ableton over the Remote Script socket.

```
Ableton MCP:   Claude -> MCP JSON-RPC -> Remote Script (TCP:9877)
ableton-cli:   Claude -> Bash -> CLI    -> bundled Remote Script (TCP:9877)
```

### Token Efficiency

| Aspect | MCP | CLI | Winner |
|--------|-----|-----|--------|
| **Fixed overhead** | 17 tool definitions in system prompt every turn (thousands of tokens) | Single `Bash` tool only. Commands learned via `--help` or skill | **CLI** |
| **Per-call cost** | JSON-RPC request/response with full parameter schema | Short shell command + concise text output | **CLI** |
| **Batch operations** | One tool call per operation | Chain with `&&` in a single Bash call | **CLI** |
| **Type safety** | JSON Schema validates parameters | No schema validation | MCP |
| **Discoverability** | Tool list auto-exposed to the model | Requires `--help` or a skill | MCP |

### Example: Set tempo + create track + fire clip

```bash
# MCP: 3 separate tool calls (3 round-trips)
mcp__ableton__set_tempo(bpm=128)
mcp__ableton__create_midi_track(index=-1)
mcp__ableton__fire_clip(track_index=0, clip_index=0)

# CLI: 1 Bash call
ableton tempo 128 && ableton track create && ableton clip fire 0 0
```

The CLI approach is significantly more token-efficient, especially in long sessions where MCP tool definitions consume context on every turn.

## Setup

### 1. Install the Ableton Remote Script

Clone or download this repository, then copy `remote_scripts/AbletonMCP_Remote_Script` into Ableton's MIDI Remote Scripts directory:

```
# macOS
~/Music/Ableton/User Library/Remote Scripts/AbletonMCP_Remote_Script/

# Windows
~\Documents\Ableton\User Library\Remote Scripts\AbletonMCP_Remote_Script\
```

In Ableton Live, go to Settings → Link, Tempo & MIDI → Control Surface and select **AbletonMCP**.

This script is based on `ahujasid/ableton-mcp` with ableton-cli-specific changes. See [`remote_scripts/README.md`](remote_scripts/README.md) for the upstream base commit and local changes.

### 2. Install the CLI

**Recommended** – install globally with a single command (requires [uv](https://docs.astral.sh/uv/)):

```bash
uv tool install git+https://github.com/ryok/ableton-cli.git
```

Alternatively, using [pipx](https://pipx.pypa.io/):

```bash
pipx install git+https://github.com/ryok/ableton-cli.git
```

<details>
<summary>For development (editable install)</summary>

```bash
git clone https://github.com/ryok/ableton-cli.git
cd ableton-cli
uv venv && uv pip install -e .
source .venv/bin/activate
```

</details>

## Usage

With Ableton Live running and the Remote Script loaded:

```bash
# Session info
ableton session

# Change tempo
ableton tempo 128

# Playback
ableton play
ableton stop
```

### Track Operations

```bash
ableton track info 0          # Details of track 0
ableton track create           # Create a MIDI track
ableton track create -i 2      # Insert at index 2
ableton track rename 0 "Bass"  # Rename track
```

### Clip Operations

```bash
# Create a clip (track 0, slot 0, 8 beats)
ableton clip create 0 0 --length 8

# Add MIDI notes
ableton clip add-notes 0 0 '[
  {"pitch": 60, "start_time": 0, "duration": 1, "velocity": 100},
  {"pitch": 64, "start_time": 1, "duration": 1, "velocity": 80},
  {"pitch": 67, "start_time": 2, "duration": 1, "velocity": 90}
]'

# Rename a clip
ableton clip rename 0 0 "Chord"

# Fire / stop a clip
ableton clip fire 0 0
ableton clip stop 0 0
```

### Browser

```bash
# Show category tree
ableton browser tree
ableton browser tree -c instruments

# Get details of a single item
ableton browser get -p "instruments/Synths/Bass"
ableton browser get -u "query:Synths#Instrument%20Rack:Bass:FileId_5116"

# List items at a path
ableton browser items "instruments/Synths"
```

### Loading Browser Items

```bash
# Load by URI
ableton load 0 "query:Synths#Instrument%20Rack:Bass:FileId_5116"

# Load a sample or browser item into a specific Session View slot
ableton load-slot 2 0 "query:UserLibrary#Samples:auto-dtm:chop_08_outro_vocal.wav"

# Load a drum kit
ableton load-drum-kit 0 "Drums/Drum Rack" "drums/acoustic/kit1"
```

### Connection Options

```bash
# Default: localhost:9877
ableton --host 192.168.1.10 --port 9877 session
```

## AI Agent Skills

This repository includes pre-built [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/skills) in the [`skills/`](skills/) directory. These enable AI agents to control Ableton Live through the CLI.

### Quick Setup

To use the skill in **another project**, copy it into your `.claude/skills/` directory:

```bash
cp -r /path/to/ableton-cli/skills/ableton-live /your/project/.claude/skills/
```

Or make it available in **all projects** as a personal skill:

```bash
cp -r /path/to/ableton-cli/skills/ableton-live ~/.claude/skills/
```

See [`skills/README.md`](skills/README.md) for more details.

## License

MIT
