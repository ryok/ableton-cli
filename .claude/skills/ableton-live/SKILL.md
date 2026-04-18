---
name: ableton-live
description: >
  Control Ableton Live from the terminal using ableton-cli.
  Use when the user wants to create tracks, clips, add MIDI notes,
  browse instruments/effects, control playback, or manipulate an Ableton Live session.
when_to_use: >
  Trigger when user mentions: Ableton, DAW, music production, MIDI, tracks, clips,
  tempo, BPM, playback, instruments, effects, drum kit, synth, audio, beat, melody, chord.
allowed-tools: Bash(ableton:*)
---

# Ableton Live CLI

Control Ableton Live via the `ableton` CLI. Requires Ableton Live running with the AbletonMCP Remote Script loaded on `localhost:9877`.

## Prerequisites

Activate the project venv before running commands:

```bash
source /Users/ryookada/work/ableton-cli/.venv/bin/activate
```

## Workflow

Always follow this order when creating music:

1. **Check session state** – `ableton session` to see current tempo, tracks, etc.
2. **Create tracks** – `ableton track create` for new MIDI tracks
3. **Rename tracks** – `ableton track rename <index> "<name>"` for clarity
4. **Load instruments** – Browse then load instruments/effects onto tracks
5. **Create clips** – `ableton clip create <track> <slot> --length <beats>`
6. **Add notes** – `ableton clip add-notes <track> <slot> '<json>'`
7. **Playback** – `ableton clip fire` or `ableton play`

## Command Reference

### Session & Transport

```bash
ableton session              # Show session info (tempo, track count, master)
ableton tempo <BPM>          # Set tempo (e.g. ableton tempo 120)
ableton play                 # Start playback
ableton stop                 # Stop playback
```

### Tracks

```bash
ableton track info <index>              # Get track details (devices, clips, etc.)
ableton track create                    # Create MIDI track at end
ableton track create -i <index>         # Create MIDI track at position
ableton track rename <index> "<name>"   # Rename a track
```

Track indices are 0-based. Use `ableton session` to check track count.

### Clips

```bash
ableton clip create <track> <slot> --length <beats>   # Create empty MIDI clip
ableton clip rename <track> <slot> "<name>"            # Rename a clip
ableton clip fire <track> <slot>                       # Start playing clip
ableton clip stop <track> <slot>                       # Stop clip
```

### Adding MIDI Notes

```bash
ableton clip add-notes <track> <slot> '<JSON array>'
```

Each note object has these fields:
- `pitch` (int): MIDI note number (0-127). Middle C = 60
- `start_time` (float): Position in beats from clip start
- `duration` (float): Length in beats
- `velocity` (int): Note velocity (1-127)
- `mute` (bool, optional): Whether note is muted (default: false)

**Example – C major chord:**
```bash
ableton clip add-notes 0 0 '[
  {"pitch": 60, "start_time": 0, "duration": 1, "velocity": 100},
  {"pitch": 64, "start_time": 0, "duration": 1, "velocity": 90},
  {"pitch": 67, "start_time": 0, "duration": 1, "velocity": 90}
]'
```

**Example – 4-bar drum pattern (kick + snare):**
```bash
ableton clip add-notes 1 0 '[
  {"pitch": 36, "start_time": 0, "duration": 0.5, "velocity": 110},
  {"pitch": 38, "start_time": 1, "duration": 0.5, "velocity": 100},
  {"pitch": 36, "start_time": 2, "duration": 0.5, "velocity": 110},
  {"pitch": 38, "start_time": 3, "duration": 0.5, "velocity": 100}
]'
```

### MIDI Note Reference

| Note  | MIDI | Note  | MIDI | Note  | MIDI |
|-------|------|-------|------|-------|------|
| C3    | 48   | C4    | 60   | C5    | 72   |
| D3    | 50   | D4    | 62   | D5    | 74   |
| E3    | 52   | E4    | 64   | E5    | 76   |
| F3    | 53   | F4    | 65   | F5    | 77   |
| G3    | 55   | G4    | 67   | G5    | 79   |
| A3    | 57   | A4    | 69   | A5    | 81   |
| B3    | 59   | B4    | 71   | B5    | 83   |

**General MIDI Drum Map (common):**
| Sound         | MIDI |
|---------------|------|
| Kick          | 36   |
| Snare         | 38   |
| Closed Hi-Hat | 42   |
| Open Hi-Hat   | 46   |
| Crash         | 49   |
| Ride          | 51   |

### Browser

```bash
ableton browser tree                           # Show full browser tree
ableton browser tree -c instruments            # Instruments only
ableton browser tree -c sounds                 # Sounds only
ableton browser tree -c drums                  # Drums only
ableton browser tree -c audio_effects          # Audio effects only
ableton browser tree -c midi_effects           # MIDI effects only

ableton browser get -p "<path>"                # Get item details by path
ableton browser get -u "<uri>"                 # Get item details by URI

ableton browser items "<path>"                 # List items at path
ableton browser items "instruments/Synths"     # Example: list synths
```

### Loading Instruments & Effects

```bash
# Load by URI (get URI from browser commands)
ableton load <track> "<uri>"

# Load drum rack + kit
ableton load-drum-kit <track> "<rack_uri>" "<kit_path>"
```

**Typical workflow to load an instrument:**
```bash
# 1. Browse available instruments
ableton browser tree -c instruments
# 2. Drill into a category
ableton browser items "instruments/Synths"
# 3. Load using the URI from the listing
ableton load 0 "query:Synths#Instrument%20Rack:Bass:FileId_5116"
```

### Connection Options

```bash
ableton --host <ip> --port <port> <command>    # Custom host/port
# Default: localhost:9877
```

## Tips

- Always call `ableton session` first to understand current state
- Create clips with enough length for your notes (`--length` in beats)
- When building complex arrangements, work one track at a time
- Use `ableton track info <index>` to verify devices and clips after changes
- Note JSON must be valid – use single quotes around the JSON array on the shell
