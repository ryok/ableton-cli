# Skills

Pre-built [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/skills) for AI agents to control Ableton Live.

## Available Skills

| Skill | Description |
|-------|-------------|
| [ableton-live](ableton-live/SKILL.md) | Full command reference for controlling Ableton Live via `ableton` CLI. Includes MIDI note tables, workflow guidance, and usage examples. |

## Installation

### For this project (already configured)

Skills are automatically available when using Claude Code in this repository. The `.claude/skills/` directory contains symlinks to the skills in this folder.

### For other projects

Copy the skill directory into your project's `.claude/skills/`:

```bash
# From your project root
mkdir -p .claude/skills
cp -r /path/to/ableton-cli/skills/ableton-live .claude/skills/
```

Or symlink it:

```bash
mkdir -p .claude/skills
ln -s /path/to/ableton-cli/skills/ableton-live .claude/skills/ableton-live
```

### As a personal skill (available in all projects)

```bash
cp -r /path/to/ableton-cli/skills/ableton-live ~/.claude/skills/
```

## Requirements

- [ableton-cli](../README.md) installed and in PATH
- Ableton Live running with this repository's bundled `remote_scripts/AbletonMCP_Remote_Script` loaded

## Creating New Skills

To add a new skill, create a directory under `skills/` with a `SKILL.md` file, then symlink it from `.claude/skills/`:

```bash
mkdir skills/my-new-skill
# Edit skills/my-new-skill/SKILL.md

# Symlink for local Claude Code use
mkdir -p .claude/skills
ln -s ../../skills/my-new-skill .claude/skills/my-new-skill
```

See [Claude Code Skills docs](https://docs.anthropic.com/en/docs/claude-code/skills) for the SKILL.md format reference.
