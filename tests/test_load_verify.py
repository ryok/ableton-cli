"""Tests for `ableton load` checking where the item actually landed.

Live's browser.load_item() reports success whatever it did, and once put an
instrument preset on a brand-new track while the target kept its old one. The
CLI now compares the session before and after. A fake connection stands in for
Live so each outcome can be staged without it.
"""
from click.testing import CliRunner

import ableton_cli.main as main


class FakeLive:
    """Tracks as {name, devices, clips}; load_browser_item runs `on_load`."""

    def __init__(self, tracks, on_load):
        self.tracks = tracks
        self.on_load = on_load

    def send_command(self, command, params=None):
        params = params or {}
        if command == "get_session_info":
            return {"track_count": len(self.tracks)}
        if command == "get_track_info":
            t = self.tracks[params["track_index"]]
            return {"name": t["name"],
                    "devices": [{"name": d} for d in t["devices"]],
                    "arrangement_clips": t.get("clips", []),
                    "clip_slots": []}
        if command == "load_browser_item":
            self.on_load(self, params["track_index"])
            return {"loaded": True, "item_name": "Basic Saw Pad.adg"}
        raise AssertionError(f"unexpected command {command}")


def _run(live, *args):
    main._conn = live  # _get_conn returns the cached connection
    try:
        return CliRunner().invoke(main.cli, list(args))
    finally:
        main._conn = None


def _tracks():
    return [{"name": "DRUMS", "devices": ["Boom Bap Kit"]},
            {"name": "CHORDS", "devices": ["Analog Soft Pad"], "clips": [{}]}]


def test_replaced_instrument_is_reported_with_the_new_devices():
    def swap(live, i):
        live.tracks[i]["devices"] = ["Basic Saw Pad"]
    result = _run(FakeLive(_tracks(), swap), "load", "1", "query:x")
    assert result.exit_code == 0, result.output
    assert "Basic Saw Pad" in result.output


def test_load_onto_a_new_track_fails_and_names_the_stray():
    """The real incident: target unchanged, a fresh track holds the preset."""
    def new_track(live, i):
        live.tracks.append({"name": "8-Basic Saw Pad", "devices": ["Basic Saw Pad"]})
    result = _run(FakeLive(_tracks(), new_track), "load", "1", "query:x")
    assert result.exit_code == 1
    assert "NEW track" in result.output
    assert "ableton track delete 2 --yes" in result.output


def test_nothing_changed_fails(monkeypatch):
    monkeypatch.setattr(main.time, "sleep", lambda s: None)
    clock = iter(range(100))
    monkeypatch.setattr(main.time, "monotonic", lambda: next(clock))
    result = _run(FakeLive(_tracks(), lambda live, i: None), "load", "1", "query:x")
    assert result.exit_code == 1
    assert "did not change" in result.output


def test_reloading_the_same_device_is_not_an_error(monkeypatch):
    monkeypatch.setattr(main.time, "sleep", lambda s: None)
    clock = iter(range(100))
    monkeypatch.setattr(main.time, "monotonic", lambda: next(clock))
    tracks = _tracks()
    tracks[1]["devices"] = ["Basic Saw Pad"]
    result = _run(FakeLive(tracks, lambda live, i: None), "load", "1", "query:x")
    assert result.exit_code == 0, result.output
    assert "already there" in result.output
