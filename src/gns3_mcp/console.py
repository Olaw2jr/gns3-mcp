"""Minimal async telnet client for driving GNS3 node consoles.

GNS3 exposes each node's console as a telnet server on the compute host. This module
opens a raw TCP connection, performs minimal telnet IAC negotiation (refusing all
options so the remote stops asking), and provides send/read-until-quiet helpers so an
agent can type CLI commands into a device and read the result.
"""

from __future__ import annotations

import asyncio
import re

# Telnet control bytes.
IAC = 255
DONT = 254
DO = 253
WONT = 252
WILL = 251
SB = 250
SE = 240


def _negotiate(data: bytes) -> tuple[bytes, bytes]:
    """Strip telnet IAC sequences from *data*; return (clean_output, reply_to_send)."""
    out = bytearray()
    reply = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b != IAC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= n:
            break
        cmd = data[i + 1]
        if cmd in (DO, DONT, WILL, WONT) and i + 2 < n:
            opt = data[i + 2]
            # Refuse everything: answer DO/DONT->WONT, WILL/WONT->DONT.
            if cmd in (DO, DONT):
                reply += bytes([IAC, WONT, opt])
            else:
                reply += bytes([IAC, DONT, opt])
            i += 3
        elif cmd == SB:
            # Skip sub-negotiation up to IAC SE.
            j = i + 2
            while j + 1 < n and not (data[j] == IAC and data[j + 1] == SE):
                j += 1
            i = j + 2
        else:
            i += 2
    return bytes(out), bytes(reply)


class ConsoleSession:
    """A single telnet console connection to a node."""

    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def __aenter__(self) -> "ConsoleSession":
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout=self.timeout
        )
        return self

    async def __aexit__(self, *_exc: object) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:  # noqa: BLE001 - best-effort close
                pass

    async def read_until_quiet(self, idle: float = 0.5, max_wait: float | None = None) -> str:
        """Read output until the stream is idle for *idle* seconds or max_wait elapses."""
        assert self._reader is not None and self._writer is not None
        max_wait = max_wait if max_wait is not None else self.timeout
        loop = asyncio.get_event_loop()
        deadline = loop.time() + max_wait
        chunks: list[str] = []
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            try:
                data = await asyncio.wait_for(self._reader.read(4096), timeout=idle)
            except asyncio.TimeoutError:
                break  # idle gap reached -> output settled
            if not data:
                break  # connection closed
            clean, reply = _negotiate(data)
            if reply:
                self._writer.write(reply)
                await self._writer.drain()
            chunks.append(clean.decode(errors="replace"))
        return "".join(chunks)

    async def send(self, command: str, newline: str = "\r\n") -> None:
        """Send a command line to the console."""
        assert self._writer is not None
        self._writer.write((command + newline).encode())
        await self._writer.drain()


_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def clean_output(text: str) -> str:
    """Strip ANSI escapes and trailing pager artifacts from console output."""
    text = _ANSI.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "")
    return text
