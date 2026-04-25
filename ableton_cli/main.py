"""Ableton Live CLI – control Ableton via the AbletonMCP Remote Script."""

import json
import sys
from typing import Any

import click

from ableton_cli.connection import AbletonConnection

# ── Shared helpers ──────────────────────────────────────────────────

_conn: AbletonConnection | None = None


def _get_conn(ctx: click.Context) -> AbletonConnection:
    global _conn
    if _conn is None:
        host = ctx.obj["host"]
        port = ctx.obj["port"]
        _conn = AbletonConnection(host, port)
        try:
            _conn.connect()
        except Exception as e:
            click.echo(f"Error: Ableton に接続できません ({host}:{port}) – {e}", err=True)
            sys.exit(1)
    return _conn


def _pp(data: dict | list) -> None:
    """Pretty-print JSON data."""
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


# ── Root group ──────────────────────────────────────────────────────

@click.group()
@click.option("--host", default="localhost", help="Ableton Remote Script host")
@click.option("--port", default=9877, type=int, help="Ableton Remote Script port")
@click.pass_context
def cli(ctx: click.Context, host: str, port: int) -> None:
    """Ableton Live CLI – control Ableton from your terminal."""
    ctx.ensure_object(dict)
    ctx.obj["host"] = host
    ctx.obj["port"] = port


# ── Session commands ────────────────────────────────────────────────

@cli.command()
@click.pass_context
def session(ctx: click.Context) -> None:
    """Show current session info (tempo, tracks, etc.)."""
    conn = _get_conn(ctx)
    result = conn.send_command("get_session_info")
    _pp(result)


@cli.command()
@click.argument("bpm", type=float)
@click.pass_context
def tempo(ctx: click.Context, bpm: float) -> None:
    """Set the session tempo (BPM)."""
    conn = _get_conn(ctx)
    conn.send_command("set_tempo", {"tempo": bpm})
    click.echo(f"Tempo set to {bpm} BPM")


@cli.command()
@click.pass_context
def play(ctx: click.Context) -> None:
    """Start playback."""
    conn = _get_conn(ctx)
    conn.send_command("start_playback")
    click.echo("Playback started")


@cli.command()
@click.pass_context
def stop(ctx: click.Context) -> None:
    """Stop playback."""
    conn = _get_conn(ctx)
    conn.send_command("stop_playback")
    click.echo("Playback stopped")


# ── Track commands ──────────────────────────────────────────────────

@cli.group()
def track() -> None:
    """Track operations (info, create, rename)."""
    pass


@track.command("info")
@click.argument("index", type=int)
@click.pass_context
def track_info(ctx: click.Context, index: int) -> None:
    """Show detailed info for a track by INDEX."""
    conn = _get_conn(ctx)
    result = conn.send_command("get_track_info", {"track_index": index})
    _pp(result)


@track.command("create")
@click.option("--index", "-i", default=-1, type=int, help="Insert position (-1 = end)")
@click.pass_context
def track_create(ctx: click.Context, index: int) -> None:
    """Create a new MIDI track."""
    conn = _get_conn(ctx)
    result = conn.send_command("create_midi_track", {"index": index})
    click.echo(f"Created MIDI track: {result.get('name', '?')} (index {result.get('index', '?')})")


@track.command("rename")
@click.argument("index", type=int)
@click.argument("name")
@click.pass_context
def track_rename(ctx: click.Context, index: int, name: str) -> None:
    """Rename a track at INDEX to NAME."""
    conn = _get_conn(ctx)
    result = conn.send_command("set_track_name", {"track_index": index, "name": name})
    click.echo(f"Track renamed to: {result.get('name', name)}")


# ── Clip commands ───────────────────────────────────────────────────

@cli.group()
def clip() -> None:
    """Clip operations (create, rename, add-notes, fire, stop)."""
    pass


@clip.command("create")
@click.argument("track_index", type=int)
@click.argument("clip_index", type=int)
@click.option("--length", "-l", default=4.0, type=float, help="Clip length in beats")
@click.pass_context
def clip_create(ctx: click.Context, track_index: int, clip_index: int, length: float) -> None:
    """Create a MIDI clip at TRACK_INDEX / CLIP_INDEX."""
    conn = _get_conn(ctx)
    conn.send_command("create_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
        "length": length,
    })
    click.echo(f"Created clip at track {track_index}, slot {clip_index} ({length} beats)")


@clip.command("rename")
@click.argument("track_index", type=int)
@click.argument("clip_index", type=int)
@click.argument("name")
@click.pass_context
def clip_rename(ctx: click.Context, track_index: int, clip_index: int, name: str) -> None:
    """Rename a clip at TRACK_INDEX / CLIP_INDEX."""
    conn = _get_conn(ctx)
    conn.send_command("set_clip_name", {
        "track_index": track_index,
        "clip_index": clip_index,
        "name": name,
    })
    click.echo(f"Clip renamed to: {name}")


@clip.command("add-notes")
@click.argument("track_index", type=int)
@click.argument("clip_index", type=int)
@click.argument("notes_json")
@click.pass_context
def clip_add_notes(ctx: click.Context, track_index: int, clip_index: int, notes_json: str) -> None:
    """Add MIDI notes to a clip. NOTES_JSON is a JSON array of note objects.

    Each note: {"pitch": 60, "start_time": 0.0, "duration": 0.25, "velocity": 100, "mute": false}

    Example: ableton clip add-notes 0 0 '[{"pitch":60,"start_time":0,"duration":1,"velocity":100}]'
    """
    conn = _get_conn(ctx)
    try:
        notes = json.loads(notes_json)
    except json.JSONDecodeError as e:
        click.echo(f"Error: invalid JSON – {e}", err=True)
        sys.exit(1)
    if not isinstance(notes, list):
        click.echo("Error: NOTES_JSON must be a JSON array", err=True)
        sys.exit(1)
    conn.send_command("add_notes_to_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
        "notes": notes,
    })
    click.echo(f"Added {len(notes)} note(s) to track {track_index}, slot {clip_index}")


@clip.command("fire")
@click.argument("track_index", type=int)
@click.argument("clip_index", type=int)
@click.pass_context
def clip_fire(ctx: click.Context, track_index: int, clip_index: int) -> None:
    """Fire (start playing) a clip."""
    conn = _get_conn(ctx)
    conn.send_command("fire_clip", {"track_index": track_index, "clip_index": clip_index})
    click.echo(f"Fired clip at track {track_index}, slot {clip_index}")


@clip.command("stop")
@click.argument("track_index", type=int)
@click.argument("clip_index", type=int)
@click.pass_context
def clip_stop(ctx: click.Context, track_index: int, clip_index: int) -> None:
    """Stop a clip."""
    conn = _get_conn(ctx)
    conn.send_command("stop_clip", {"track_index": track_index, "clip_index": clip_index})
    click.echo(f"Stopped clip at track {track_index}, slot {clip_index}")


# ── Browser commands ────────────────────────────────────────────────

@cli.group()
def browser() -> None:
    """Browse Ableton's instrument / effect library."""
    pass


@browser.command("tree")
@click.option("--category", "-c", default="all",
              type=click.Choice(["all", "instruments", "sounds", "drums", "audio_effects", "midi_effects"]),
              help="Category to show")
@click.pass_context
def browser_tree(ctx: click.Context, category: str) -> None:
    """Show the browser category tree."""
    conn = _get_conn(ctx)
    result = conn.send_command("get_browser_tree", {"category_type": category})

    for cat in result.get("categories", []):
        _print_tree(cat)


def _print_tree(item: dict, indent: int = 0) -> None:
    prefix = "  " * indent
    name = item.get("name", "?")
    uri = item.get("uri", "")
    marker = "📁" if item.get("is_folder") else ("🎹" if item.get("is_loadable") else "·")
    line = f"{prefix}{marker} {name}"
    if uri:
        line += f"  ({uri})"
    click.echo(line)
    for child in item.get("children", []):
        _print_tree(child, indent + 1)


@browser.command("get")
@click.option("--uri", "-u", default=None, help="URI of the browser item")
@click.option("--path", "-p", default=None, help="Path to the browser item (e.g. 'instruments/Synths/Bass')")
@click.pass_context
def browser_get(ctx: click.Context, uri: str | None, path: str | None) -> None:
    """Get details of a single browser item by URI or path."""
    if not uri and not path:
        click.echo("Error: --uri or --path のどちらかを指定してください", err=True)
        sys.exit(1)
    conn = _get_conn(ctx)
    params: dict[str, Any] = {}
    if uri:
        params["uri"] = uri
    if path:
        params["path"] = path
    result = conn.send_command("get_browser_item", params)
    if result.get("found"):
        _pp(result.get("item", {}))
    else:
        error = result.get("error", "Item not found")
        click.echo(f"Not found: {error}", err=True)
        sys.exit(1)


@browser.command("items")
@click.argument("path")
@click.pass_context
def browser_items(ctx: click.Context, path: str) -> None:
    """List browser items at PATH (e.g. 'instruments/Synths')."""
    conn = _get_conn(ctx)
    result = conn.send_command("get_browser_items_at_path", {"path": path})

    if "error" in result:
        click.echo(f"Error: {result['error']}", err=True)
        sys.exit(1)

    items = result.get("items", [])
    if not items:
        click.echo("No items found.")
        return

    for item in items:
        marker = "📁" if item.get("is_folder") else ("🎹" if item.get("is_loadable") else "·")
        uri = item.get("uri", "")
        line = f"  {marker} {item.get('name', '?')}"
        if uri:
            line += f"  ({uri})"
        click.echo(line)


# ── Load commands ───────────────────────────────────────────────────

@cli.command("load")
@click.argument("track_index", type=int)
@click.argument("uri")
@click.pass_context
def load_instrument(ctx: click.Context, track_index: int, uri: str) -> None:
    """Load an instrument or effect onto a track by URI."""
    conn = _get_conn(ctx)
    result = conn.send_command("load_browser_item", {
        "track_index": track_index,
        "item_uri": uri,
    })
    if result.get("loaded"):
        click.echo(f"Loaded '{result.get('item_name', uri)}' on track {track_index}")
    else:
        click.echo(f"Failed to load: {uri}", err=True)


@cli.command("load-slot")
@click.argument("track_index", type=int)
@click.argument("clip_index", type=int)
@click.argument("uri")
@click.pass_context
def load_slot(ctx: click.Context, track_index: int, clip_index: int, uri: str) -> None:
    """Load a browser item onto a specific Session View clip slot."""
    conn = _get_conn(ctx)
    result = conn.send_command("load_browser_item_to_slot", {
        "track_index": track_index,
        "clip_index": clip_index,
        "item_uri": uri,
    })
    if result.get("loaded"):
        item_name = result.get("item_name", uri)
        click.echo(f"Loaded '{item_name}' on track {track_index}, slot {clip_index}")
    else:
        click.echo(f"Failed to load: {uri}", err=True)


@cli.command("load-drum-kit")
@click.argument("track_index", type=int)
@click.argument("rack_uri")
@click.argument("kit_path")
@click.pass_context
def load_drum_kit(ctx: click.Context, track_index: int, rack_uri: str, kit_path: str) -> None:
    """Load a drum rack and kit onto a track.

    RACK_URI: URI of the drum rack.
    KIT_PATH: Browser path to the drum kit (e.g. 'drums/acoustic/kit1').
    """
    conn = _get_conn(ctx)

    # Step 1: Load the drum rack
    result = conn.send_command("load_browser_item", {
        "track_index": track_index,
        "item_uri": rack_uri,
    })
    if not result.get("loaded"):
        click.echo(f"Failed to load drum rack: {rack_uri}", err=True)
        sys.exit(1)

    # Step 2: Find loadable kits at the path
    kit_result = conn.send_command("get_browser_items_at_path", {"path": kit_path})
    if "error" in kit_result:
        click.echo(f"Drum rack loaded, but kit not found: {kit_result['error']}", err=True)
        sys.exit(1)

    loadable = [i for i in kit_result.get("items", []) if i.get("is_loadable")]
    if not loadable:
        click.echo(f"No loadable drum kits found at '{kit_path}'", err=True)
        sys.exit(1)

    # Step 3: Load the first kit
    kit_uri = loadable[0].get("uri")
    conn.send_command("load_browser_item", {
        "track_index": track_index,
        "item_uri": kit_uri,
    })
    click.echo(f"Loaded drum rack + kit '{loadable[0].get('name')}' on track {track_index}")


# ── Entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
