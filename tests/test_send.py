"""Tests for the Remote Script's set_track_send and set_track_volume argument checks.

The handler is called unbound on a stand-in for the ControlSurface, so the
argument checks can run without Live. A call with no level used to return the
current level as if it had been set.
"""
import types

import pytest

from test_volume import _load

MCP = _load().AbletonMCP


class FakeParam:
    min, max = 0.0, 1.0

    def __init__(self, value):
        self.value = value

    def str_for_value(self, v):
        return "%.2f" % v


def _surface(send_value=0.5):
    track = types.SimpleNamespace(
        name="CHOPS", mixer_device=types.SimpleNamespace(sends=[FakeParam(send_value)]))
    song = types.SimpleNamespace(tracks=[track],
                                 return_tracks=[types.SimpleNamespace(name="A-Reverb")])
    surface = types.SimpleNamespace(_song=song, log_message=lambda msg: None)
    surface._track_at = lambda i: MCP._track_at(surface, i)
    return surface, track


def test_send_without_a_level_is_rejected_and_leaves_the_send_alone():
    surface, track = _surface(0.5)
    with pytest.raises(Exception, match="Pass db or value"):
        MCP._set_track_send(surface, 0, 0, None, None)
    assert track.mixer_device.sends[0].value == 0.5


def test_volume_without_a_level_is_rejected_and_leaves_the_fader_alone():
    surface, track = _surface()
    track.mixer_device.volume = FakeParam(0.85)
    with pytest.raises(Exception, match="Pass db or value"):
        MCP._set_track_volume(surface, 0, None, None)
    assert track.mixer_device.volume.value == 0.85


def test_send_with_both_levels_is_rejected():
    surface, _ = _surface()
    with pytest.raises(Exception, match="not both"):
        MCP._set_track_send(surface, 0, 0, 0.3, -20)


def test_send_by_value_is_clamped_and_names_the_return():
    surface, track = _surface()
    result = MCP._set_track_send(surface, 0, 0, 1.7, None)
    assert track.mixer_device.sends[0].value == 1.0
    assert result["return"] == "A-Reverb"
