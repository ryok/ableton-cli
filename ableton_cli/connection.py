"""Ableton Live socket connection handler."""

import json
import socket
import time
from typing import Any


class AbletonConnection:
    """Manages TCP socket connection to the AbletonMCP Remote Script."""

    def __init__(self, host: str = "localhost", port: int = 9877):
        self.host = host
        self.port = port
        self.sock: socket.socket | None = None

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

        is_modifying = command_type in {
            "create_midi_track", "create_audio_track", "set_track_name",
            "create_clip", "add_notes_to_clip", "set_clip_name",
            "set_tempo", "fire_clip", "stop_clip", "set_device_parameter",
            "start_playback", "stop_playback", "load_browser_item",
            "load_browser_item_to_slot",
        }

        try:
            assert self.sock is not None
            self.sock.sendall(json.dumps(command).encode("utf-8"))
            if is_modifying:
                time.sleep(0.1)
            response_data = self._receive_full_response()
            response = json.loads(response_data.decode("utf-8"))
            if response.get("status") == "error":
                raise RuntimeError(response.get("message", "Unknown error from Ableton"))
            if is_modifying:
                time.sleep(0.1)
            return response.get("result", {})
        except (ConnectionError, BrokenPipeError, ConnectionResetError, socket.timeout) as e:
            self.sock = None
            raise ConnectionError(f"Lost connection to Ableton: {e}") from e
        except json.JSONDecodeError as e:
            self.sock = None
            raise RuntimeError(f"Invalid response from Ableton: {e}") from e
