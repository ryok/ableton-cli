"""Tests for the volume helpers in the Remote Script.

The Remote Script imports _Framework at module level, which only exists inside
Live, so the module is loaded here with that dependency stubbed. The functions
under test touch nothing from Live themselves — that separation is the reason
they can be tested at all.
"""
import importlib.util
import sys
import types
from pathlib import Path

import pytest

SCRIPT = (Path(__file__).parent.parent / "remote_scripts"
          / "AbletonMCP_Remote_Script" / "__init__.py")


def _load():
    framework = types.ModuleType("_Framework")
    cs = types.ModuleType("_Framework.ControlSurface")
    cs.ControlSurface = object
    sys.modules.setdefault("_Framework", framework)
    sys.modules.setdefault("_Framework.ControlSurface", cs)
    spec = importlib.util.spec_from_file_location("_abletonmcp_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mcp = _load()


# ── parse_display_db ────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("-4.6 dB", -4.6),
    ("0.0 dB", 0.0),
    ("6 dB", 6.0),
    ("-4.6dB", -4.6),
    ("  -4.6 dB  ", -4.6),
])
def test_parses_normal_displays(text, expected):
    assert mcp.parse_display_db(text) == pytest.approx(expected)


def test_parses_comma_decimal_separator():
    """Some locales display "-4,6 dB". float() would raise on that."""
    assert mcp.parse_display_db("-4,6 dB") == pytest.approx(-4.6)


@pytest.mark.parametrize("text", ["-inf dB", "-INF dB", "-∞ dB"])
def test_bottom_of_fader_reads_as_silence(text):
    assert mcp.parse_display_db(text) == -999.0


def test_unparseable_does_not_raise():
    """An unrecognised format must not abort a volume change mid-bisection."""
    assert mcp.parse_display_db("who knows") == -999.0


# ── solve_for_db ────────────────────────────────────────────────────

def _fader(lo_db=-70.0, hi_db=6.0):
    """A monotonic stand-in for Live's volume curve, quantised like the display."""
    def as_db(v):
        v = max(0.0, min(1.0, v))
        return round(lo_db + (hi_db - lo_db) * (v ** 0.5), 1)
    return as_db


def test_hits_the_requested_db():
    value, clamped = mcp.solve_for_db(-4.6, 0.0, 1.0, _fader())
    assert not clamped
    assert _fader()(value) == pytest.approx(-4.6, abs=0.05)


def test_hits_zero_db():
    value, clamped = mcp.solve_for_db(0.0, 0.0, 1.0, _fader())
    assert not clamped
    assert _fader()(value) == pytest.approx(0.0, abs=0.05)


def test_reports_clamped_above_range():
    """Asking for more than the fader has must not be reported as success."""
    value, clamped = mcp.solve_for_db(20.0, 0.0, 1.0, _fader())
    assert clamped
    assert value == pytest.approx(1.0, abs=0.01)


def test_reports_clamped_below_range():
    value, clamped = mcp.solve_for_db(-200.0, 0.0, 1.0, _fader())
    assert clamped
    assert value == pytest.approx(0.0, abs=0.01)


def test_survives_a_fader_that_reads_inf_at_the_bottom():
    """The real curve returns "-inf" near zero, which parses to -999."""
    base = _fader()

    def as_db(v):
        return -999.0 if v < 0.02 else base(v)

    value, clamped = mcp.solve_for_db(-10.0, 0.0, 1.0, as_db)
    assert not clamped
    assert as_db(value) == pytest.approx(-10.0, abs=0.05)


# ── the command table both sides depend on ──────────────────────────

def test_read_commands_are_not_marked_modifying():
    """get_clip_notes needs the main thread but must not get settling delays."""
    assert "get_clip_notes" in mcp.MAIN_THREAD_COMMANDS
    assert "get_clip_notes" not in mcp.MODIFYING_COMMANDS


def test_every_modifying_command_runs_on_the_main_thread():
    assert mcp.MODIFYING_COMMANDS <= mcp.MAIN_THREAD_COMMANDS


def test_client_fallback_covers_every_modifying_command():
    """The fallback is used against older scripts; it must not miss commands.

    Five commands once shipped without their delays because this list and the
    script's were maintained separately.
    """
    from ableton_cli.connection import _FALLBACK_MODIFYING
    missing = mcp.MODIFYING_COMMANDS - _FALLBACK_MODIFYING
    assert not missing, f"missing from the client fallback: {sorted(missing)}"
