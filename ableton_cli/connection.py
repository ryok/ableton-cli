"""Ableton Live socket connection handler."""

import json
import socket
import time
from typing import Any


class AbletonError(RuntimeError):
    """An error reported by Ableton, as opposed to a bug in this CLI.

    Kept distinct so the CLI can print these as one readable line while letting
    genuine programming errors surface with their traceback intact.
    """


# Fallback for Remote Scripts too old to answer get_command_list. Newer scripts
# own the authoritative set; see AbletonConnection._modifying_commands.
_FALLBACK_MODIFYING = frozenset({
    "create_midi_track", "create_audio_track", "set_track_name",
    "create_clip", "add_notes_to_clip", "set_clip_name", "set_clip_loop",
    "set_clip_warp",
    "set_tempo", "fire_clip", "stop_clip", "set_device_parameter",
    "start_playback", "stop_playback", "load_browser_item",
    "load_browser_item_to_slot", "load_browser_item_to_arrangement",
    "set_track_mute", "set_track_solo", "set_track_volume",
    "delete_track", "duplicate_clip_to_arrangement",
    "set_device_parameter", "delete_device",
})


class AbletonConnection:
    """Manages TCP socket connection to the AbletonMCP Remote Script."""

    def __init__(self, host: str = "localhost", port: int = 9877):
        self.host = host
        self.port = port
        self.sock: socket.socket | None = None
        self._modifying: frozenset[str] | None = None

    def connect(self) -> None:
        if self.sock:
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def disconnect(self) -> None:
        if self.sock:
            self.sock.close()
            self.sock = None

    def _receive_full_response(self) -> bytes:
        assert self.sock is not None
        chunks: list[bytes] = []
        self.sock.settimeout(15.0)
        while True:
            try:
                chunk = self.sock.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                if not chunks:
                    raise ConnectionError("Connection closed before receiving data")
                break
            chunks.append(chunk)
            data = b"".join(chunks)
            try:
                json.loads(data.decode("utf-8"))
                return data
            except json.JSONDecodeError:
                continue
        if chunks:
            data = b"".join(chunks)
            json.loads(data.decode("utf-8"))  # validate or raise
            return data
        raise ConnectionError("No data received")

    def send_command(self, command_type: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.sock:
            self.connect()

        command = {"type": command_type, "params": params or {}}
        is_modifying = command_type in self._modifying_commands()

        try:
            assert self.sock is not None
            self.sock.sendall(json.dumps(command).encode("utf-8"))
            if is_modifying:
                time.sleep(0.1)
            response_data = self._receive_full_response()
            response = json.loads(response_data.decode("utf-8"))
            if response.get("status") == "error":
                raise AbletonError(response.get("message", "Unknown error from Ableton"))
            if is_modifying:
                time.sleep(0.1)
            return response.get("result", {})
        except (ConnectionError, BrokenPipeError, ConnectionResetError, socket.timeout) as e:
            self.sock = None
            raise ConnectionError(f"Lost connection to Ableton: {e}") from e
        except json.JSONDecodeError as e:
            self.sock = None
            raise AbletonError(f"Invalid response from Ableton: {e}") from e

    def _modifying_commands(self) -> frozenset[str]:
        """Which commands mutate Live's state, and so need the settling delays.

        The Remote Script is the authority: it has to know this anyway to decide
        what runs on the main thread, and keeping a second copy here is what let
        five commands ship without their delays. Ask it once per process and
        cache; fall back to the local set when talking to an older script that
        does not answer.
        """
        if self._modifying is None:
            try:
                self.sock.sendall(json.dumps(
                    {"type": "get_command_list", "params": {}}).encode("utf-8"))
                response = json.loads(self._receive_full_response().decode("utf-8"))
                names = (response.get("result") or {}).get("modifying")
                self._modifying = frozenset(names) if names else _FALLBACK_MODIFYING
            except Exception:
                self._modifying = _FALLBACK_MODIFYING
        return self._modifying
