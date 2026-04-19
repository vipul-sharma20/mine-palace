from __future__ import annotations

import socket
import struct
import time


class RconClient:
    def __init__(self, host: str, port: int, password: str, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self._socket: socket.socket | None = None
        self._request_id = 0

    def __enter__(self) -> "RconClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def connect(self) -> None:
        self._socket = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self._socket.settimeout(self.timeout)
        response = self._send_packet(3, self.password)
        if response[0] == -1:
            raise RuntimeError("RCON authentication failed")

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def command(self, command: str) -> str:
        response = self._send_packet(2, command)
        return response[2]

    def command_many(
        self,
        commands: list[str],
        *,
        rate_limit_ms: int = 0,
        progress_every: int = 25,
    ) -> None:
        total = len(commands)
        for index, command in enumerate(commands, start=1):
            if not command or command.startswith("#"):
                continue
            self.command(command)
            if progress_every and index % progress_every == 0:
                print(f"Applied {index}/{total} commands")
            if rate_limit_ms > 0:
                time.sleep(rate_limit_ms / 1000)

    def _send_packet(self, packet_type: int, body: str) -> tuple[int, int, str]:
        if self._socket is None:
            raise RuntimeError("RCON socket is not connected")

        self._request_id += 1
        request_id = self._request_id
        encoded = body.encode("utf-8")
        packet = struct.pack("<iii", len(encoded) + 10, request_id, packet_type) + encoded + b"\x00\x00"
        self._socket.sendall(packet)
        return self._read_packet()

    def _read_packet(self) -> tuple[int, int, str]:
        if self._socket is None:
            raise RuntimeError("RCON socket is not connected")

        header = self._recv_exact(4)
        size = struct.unpack("<i", header)[0]
        payload = self._recv_exact(size)
        request_id, packet_type = struct.unpack("<ii", payload[:8])
        body = payload[8:-2].decode("utf-8", errors="ignore")
        return request_id, packet_type, body

    def _recv_exact(self, size: int) -> bytes:
        if self._socket is None:
            raise RuntimeError("RCON socket is not connected")

        chunks = []
        remaining = size
        while remaining:
            chunk = self._socket.recv(remaining)
            if not chunk:
                raise RuntimeError("RCON connection closed unexpectedly")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)
