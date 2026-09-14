"""Ableton Live CLI – control Ableton via the AbletonMCP Remote Script."""

import json
import sys
from pathlib import Path
from typing import Any

import click

from ableton_cli.connection import AbletonConnection, AbletonError

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


class _Cli(click.Group):
    """Turn Ableton-reported errors into one readable line instead of a traceback.

    The most common one is "Unknown command", which means the CLI is newer than
    the AbletonMCP script Live currently has loaded — so say that outright
    rather than making the user read a stack trace to find out.

    Only AbletonError is caught. Bugs in this CLI raise ordinary exceptions and
    keep their traceback, which is what you want when debugging them.
    """

    def invoke(self, ctx: click.Context) -> Any:
        try:
            return super().invoke(ctx)
        except AbletonError as e:
            msg = str(e)
            click.echo(f"Error: {msg}", err=True)
            if msg.startswith("Unknown command"):
                click.echo(
                    "Live is running an older AbletonMCP script. Copy "
                    "remote_scripts/AbletonMCP_Remote_Script/__init__.py over the "
                    "installed one, then reload it in Live: Preferences > "
                    "Link/Tempo/MIDI, set the AbletonMCP Control Surface to None "
                    "and back. Restarting Live also works.", err=True)
            sys.exit(1)


# ── Root group ──────────────────────────────────────────────────────

@click.group(cls=_Cli)
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
@click.option("--audio", is_flag=True, help="Create an audio track instead of MIDI")
@click.pass_context
def track_create(ctx: click.Context, index: int, audio: bool) -> None:
    """Create a new track (MIDI by default, or --audio).

    Sample clips (load-arrangement / load-slot) need an audio track; Live
    refuses to put an audio clip on a MIDI track.
    """
    conn = _get_conn(ctx)
    command = "create_audio_track" if audio else "create_midi_track"
    result = conn.send_command(command, {"index": index})
    kind = "audio" if audio else "MIDI"
    click.echo(f"Created {kind} track: {result.get('name', '?')} (index {result.get('index', '?')})")


@track.command("rename")
@click.argument("index", type=int)
@click.argument("name")
@click.pass_context
def track_rename(ctx: click.Context, index: int, name: str) -> None:
    """Rename a track at INDEX to NAME."""
    conn = _get_conn(ctx)
    result = conn.send_command("set_track_name", {"track_index": index, "name": name})
    click.echo(f"Track renamed to: {result.get('name', name)}")


@track.command("mute")
@click.argument("index", type=int)
@click.option("--off", is_flag=True, help="Unmute instead")
@click.pass_context
def track_mute(ctx: click.Context, index: int, off: bool) -> None:
    """Mute (or with --off, unmute) a track at INDEX."""
    conn = _get_conn(ctx)
    result = conn.send_command("set_track_mute", {"track_index": index, "mute": not off})
    state = "muted" if result.get("mute") else "unmuted"
    click.echo(f"{result.get('name', index)}: {state}")


@track.command("solo")
@click.argument("index", type=int)
@click.option("--off", is_flag=True, help="Unsolo instead")
@click.pass_context
def track_solo(ctx: click.Context, index: int, off: bool) -> None:
    """Solo (or with --off, unsolo) a track at INDEX."""
    conn = _get_conn(ctx)
    result = conn.send_command("set_track_solo", {"track_index": index, "solo": not off})
    state = "soloed" if result.get("solo") else "unsoloed"
    click.echo(f"{result.get('name', index)}: {state}")


@track.command("volume")
@click.argument("index", type=int)
@click.option("--db", type=float, help="Set volume in dB (what the mixer displays)")
@click.option("--value", type=float, help="Set the raw 0-1 parameter instead")
@click.pass_context
def track_volume(ctx: click.Context, index: int, db: float | None, value: float | None) -> None:
    """Set the volume of the track at INDEX.

    --db is usually what you want: Live's volume parameter is 0-1 on a
    non-linear curve, so 0.85 means 0 dB and there is no simple conversion.
    """
    if db is None and value is None:
        click.echo("Error: pass --db or --value", err=True)
        sys.exit(1)
    if db is not None and value is not None:
        click.echo("Error: pass --db or --value, not both", err=True)
        sys.exit(1)
    conn = _get_conn(ctx)
    result = conn.send_command("set_track_volume",
                               {"track_index": index, "db": db, "value": value})
    raw = result.get("value")
    shown = f"{raw:.4f}" if isinstance(raw, (int, float)) else "?"
    click.echo(f"{result.get('name', index)}: {result.get('display')} (value {shown})")
    if result.get("clamped"):
        click.echo(f"Note: {db} dB is outside this fader's range; "
                   f"it stopped at {result.get('display')}.", err=True)


@track.command("delete")
@click.argument("index", type=int)
@click.option("--yes", is_flag=True, help="Skip the confirmation prompt")
@click.pass_context
def track_delete(ctx: click.Context, index: int, yes: bool) -> None:
    """Delete the track at INDEX. This cannot be undone from the CLI."""
    conn = _get_conn(ctx)
    if not yes:
        info = conn.send_command("get_track_info", {"track_index": index})
        click.confirm(f"Delete track {index} ({info.get('name')})?", abort=True)
    result = conn.send_command("delete_track", {"track_index": index})
    click.echo(f"Deleted {result.get('deleted')} ({result.get('track_count')} tracks left)")


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


@clip.command("loop")
@click.argument("track_index", type=int)
@click.argument("clip_index", type=int)
@click.option("--bars", "-b", required=True, type=float, help="Loop length in bars")
@click.option("--start-bar", default=0.0, type=float, help="Loop start, in bars (default 0)")
@click.option("--beats-per-bar", default=4.0, type=float, help="Beats per bar (default 4 = 4/4)")
@click.option("--session", "is_session", is_flag=True,
              help="Target a Session View clip slot instead of an Arrangement clip")
@click.option("--off", is_flag=True, help="Turn looping off (still trims markers to the region)")
@click.pass_context
def clip_loop(ctx: click.Context, track_index: int, clip_index: int, bars: float,
              start_bar: float, beats_per_bar: float, is_session: bool, off: bool) -> None:
    """Loop a clip to a whole number of BARS from START_BAR.

    load-arrangement drops the full sample, whose warped length is rarely an
    integer number of bars, so layers drift apart. Loop every layer to the
    same bar count and they stay phase-aligned. Bars are converted to beats
    with --beats-per-bar (4 = 4/4).
    """
    conn = _get_conn(ctx)
    loop_start = start_bar * beats_per_bar
    loop_end = (start_bar + bars) * beats_per_bar
    result = conn.send_command("set_clip_loop", {
        "track_index": track_index,
        "clip_index": clip_index,
        "loop_start": loop_start,
        "loop_end": loop_end,
        "looping": not off,
        "view": "session" if is_session else "arrangement",
    })
    ls, le = result.get("loop_start"), result.get("loop_end")
    state = "looping" if result.get("looping") else "loop off"
    click.echo(f"{result.get('name', clip_index)}: {state} {ls}-{le} beats "
               f"({(le - ls) / beats_per_bar:.2f} bars)")


@clip.command("warp")
@click.argument("track_index", type=int)
@click.argument("clip_index", type=int)
@click.option("--off", is_flag=True, help="Turn warp off instead of on")
@click.option("--mode", type=int, default=None,
              help="Warp mode enum (0=Beats 1=Tones 2=Texture 3=Re-Pitch 4=Complex 6=Complex Pro)")
@click.option("--session", "is_session", is_flag=True, help="Target a Session View clip slot")
@click.pass_context
def clip_warp(ctx: click.Context, track_index: int, clip_index: int, off: bool,
              mode: int | None, is_session: bool) -> None:
    """Turn warp on (or --off) for an audio clip.

    Warp must be on for `clip loop --bars` to mean bars on the session grid;
    an unwarped sample's beats are just seconds.
    """
    conn = _get_conn(ctx)
    result = conn.send_command("set_clip_warp", {
        "track_index": track_index,
        "clip_index": clip_index,
        "warping": not off,
        "warp_mode": mode,
        "view": "session" if is_session else "arrangement",
    })
    state = "warp on" if result.get("warping") else "warp off"
    click.echo(f"{result.get('name', clip_index)}: {state} (mode {result.get('warp_mode')})")


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


@clip.command("to-arrangement")
@click.argument("track_index", type=int)
@click.argument("clip_index", type=int)
@click.argument("start_time", type=float)
@click.pass_context
def clip_to_arrangement(ctx: click.Context, track_index: int, clip_index: int,
                        start_time: float) -> None:
    """Copy a Session clip into the Arrangement at START_TIME (in beats).

    The Live API cannot build Arrangement clips from scratch, so a Session clip
    has to exist first; this duplicates it across.
    """
    conn = _get_conn(ctx)
    result = conn.send_command("duplicate_clip_to_arrangement", {
        "track_index": track_index,
        "clip_index": clip_index,
        "start_time": start_time,
    })
    click.echo(f"{result.get('name')}: '{result.get('clip')}' -> arrangement "
               f"at beat {result.get('start_time')}")


@clip.command("notes")
@click.argument("track_index", type=int)
@click.argument("clip_index", type=int)
@click.option("--count", is_flag=True, help="Print only the note count")
@click.pass_context
def clip_notes(ctx: click.Context, track_index: int, clip_index: int, count: bool) -> None:
    """Read the notes back out of a clip, for verification."""
    conn = _get_conn(ctx)
    result = conn.send_command("get_clip_notes",
                               {"track_index": track_index, "clip_index": clip_index})
    if count:
        click.echo(f"{result.get('name')}: {len(result.get('notes', []))} note(s), "
                   f"{result.get('length')} beats")
    else:
        _pp(result)


@clip.command("add-notes")
@click.argument("track_index", type=int)
@click.argument("clip_index", type=int)
@click.argument("notes_json", required=False)
@click.option("--file", "-f", "notes_file", type=click.Path(exists=True, dir_okay=False),
              help="Read the note array from a JSON file instead of the argument")
@click.pass_context
def clip_add_notes(ctx: click.Context, track_index: int, clip_index: int,
                   notes_json: str | None, notes_file: str | None) -> None:
    """Add MIDI notes to a clip. NOTES_JSON is a JSON array of note objects.

    Each note: {"pitch": 60, "start_time": 0.0, "duration": 0.25, "velocity": 100, "mute": false}

    Example: ableton clip add-notes 0 0 '[{"pitch":60,"start_time":0,"duration":1,"velocity":100}]'

    Use --file for anything large. A few hundred notes already overflow the
    shell's argument limit, which otherwise forces callers to chunk by hand.
    """
    conn = _get_conn(ctx)
    if notes_file:
        notes_json = Path(notes_file).read_text(encoding="utf-8")
    elif notes_json is None:
        click.echo("Error: pass NOTES_JSON or --file", err=True)
        sys.exit(1)
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


# ── Device commands ─────────────────────────────────────────────────

def _track_arg(value: str) -> int:
    """A track argument: an integer index, or 'master'/'m' for the master (-1)."""
    if value.lower() in ("master", "m"):
        return -1
    try:
        return int(value)
    except ValueError:
        raise click.BadParameter("TRACK must be an integer index or 'master'")


@cli.group()
def device() -> None:
    """Device operations (params, set, delete). TRACK may be 'master'."""
    pass


@device.command("params")
@click.argument("track")
@click.argument("device_index", type=int)
@click.pass_context
def device_params(ctx: click.Context, track: str, device_index: int) -> None:
    """List a device's parameters (index, name, value, range).

    Read this to know what to turn, and to confirm a change afterwards.
    """
    conn = _get_conn(ctx)
    result = conn.send_command("get_device_parameters", {
        "track_index": _track_arg(track), "device_index": device_index})
    click.echo(f"{result.get('track')} / {result.get('device')}:")
    for p in result.get("parameters", []):
        click.echo(f"  [{p['index']:>2}] {p['name']}: {p['display']} "
                   f"(value {p['value']:.3f}, range {p['min']:.2f}..{p['max']:.2f})")


@device.command("set", context_settings={"ignore_unknown_options": True})
@click.argument("track")
@click.argument("device_index", type=int)
@click.argument("parameter")
@click.argument("value", type=float)
@click.pass_context
def device_set(ctx: click.Context, track: str, device_index: int,
               parameter: str, value: float) -> None:
    """Set a device PARAMETER (its index or name) to VALUE.

    Value is clamped to the parameter's range. Quote names with spaces.
    """
    conn = _get_conn(ctx)
    result = conn.send_command("set_device_parameter", {
        "track_index": _track_arg(track), "device_index": device_index,
        "parameter": parameter, "value": value})
    click.echo(f"{result.get('device')} / {result.get('parameter')}: "
               f"{result.get('display')} (value {result.get('value'):.3f})")
    if result.get("clamped"):
        click.echo("Note: value was clamped to the parameter's range.", err=True)


@device.command("delete")
@click.argument("track")
@click.argument("device_index", type=int)
@click.pass_context
def device_delete(ctx: click.Context, track: str, device_index: int) -> None:
    """Delete the device at DEVICE_INDEX from TRACK's chain."""
    conn = _get_conn(ctx)
    result = conn.send_command("delete_device", {
        "track_index": _track_arg(track), "device_index": device_index})
    click.echo(f"Deleted {result.get('deleted')} "
               f"({result.get('device_count')} left on {result.get('track')})")


@cli.command("load-master")
@click.argument("uri")
@click.pass_context
def load_master(ctx: click.Context, uri: str) -> None:
    """Load an audio effect onto the master track (whole-mix processing).

    For glue/tape/vinyl across the whole mix. The master takes audio effects
    only — instruments are ignored by Live.
    """
    conn = _get_conn(ctx)
    result = conn.send_command("load_browser_item", {
        "track_index": -1,
        "item_uri": uri,
    })
    if result.get("loaded"):
        click.echo(f"Loaded '{result.get('item_name', uri)}' on master")
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


@cli.command("load-arrangement")
@click.argument("track_index", type=int)
@click.argument("start_time", type=float)
@click.argument("source")
@click.pass_context
def load_arrangement(ctx: click.Context, track_index: int, start_time: float, source: str) -> None:
    """Load an audio file or browser item into Arrangement View at START_TIME in beats."""
    conn = _get_conn(ctx)
    params: dict[str, Any] = {
        "track_index": track_index,
        "start_time": start_time,
    }
    source_path = Path(source).expanduser()
    if source_path.exists():
        params["file_path"] = str(source_path.resolve())
    else:
        params["item_uri"] = source

    result = conn.send_command("load_browser_item_to_arrangement", {
        **params,
    })
    if result.get("loaded"):
        item_name = result.get("item_name", source)
        click.echo(f"Loaded '{item_name}' on track {track_index} at beat {start_time}")
    else:
        click.echo(f"Failed to load: {source}", err=True)


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
