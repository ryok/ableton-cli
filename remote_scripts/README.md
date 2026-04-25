# Bundled Ableton Remote Script

This directory contains the Ableton Remote Script that ableton-cli expects to run inside Ableton Live.

It is based on [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) commit `e0083285426dedb5c93ce8a532ecfbb25ae9a3ca`, with ableton-cli-specific changes.

## Current Changes From Upstream

- Adds the `load_browser_item_to_slot` command used by `ableton load-slot`.
- Expands browser URI lookup to include additional Ableton browser categories such as clips, samples, packs, plugins, user library, and user folders.

Install `AbletonMCP_Remote_Script/` into Ableton's MIDI Remote Scripts directory and select **AbletonMCP** as the Control Surface.
