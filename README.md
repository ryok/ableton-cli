# ableton-cli

A CLI tool to control Ableton Live from your terminal. Communicates with the [AbletonMCP](https://github.com/ahujasid/ableton-mcp) Remote Script over TCP sockets.

[日本語版 README](README.ja.md)

## Setup

### 1. Install the Ableton Remote Script

Copy the `AbletonMCP_Remote_Script` folder from [AbletonMCP](https://github.com/ahujasid/ableton-mcp) into Ableton's MIDI Remote Scripts directory:

```
# macOS
~/Music/Ableton/User Library/Remote Scripts/AbletonMCP_Remote_Script/

# Windows
~\Documents\Ableton\User Library\Remote Scripts\AbletonMCP_Remote_Script\
```

In Ableton Live, go to Settings → Link, Tempo & MIDI → Control Surface and select **AbletonMCP**.

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

### Loading Instruments / Effects

```bash
# Load by URI
ableton load 0 "query:Synths#Instrument%20Rack:Bass:FileId_5116"

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
