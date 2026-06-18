"""Tests for the telnet console proxy against a local fake telnet server."""

import asyncio

import pytest

from gns3_mcp.console import IAC, WILL, ConsoleSession, _negotiate, clean_output


def test_negotiate_strips_iac_and_refuses_options():
    # IAC WILL ECHO(1) + visible text 'hi'
    data = bytes([IAC, WILL, 1]) + b"hi"
    clean, reply = _negotiate(data)
    assert clean == b"hi"
    # WILL -> we answer DONT
    assert reply == bytes([IAC, 254, 1])  # IAC DONT ECHO


def test_clean_output_strips_ansi():
    assert clean_output("\x1b[2J\x1b[1;1HRouter#") == "Router#"


@pytest.mark.asyncio
async def test_send_and_read_roundtrip():
    received: list[bytes] = []

    async def handle(reader, writer):
        # Greet with a telnet negotiation + prompt.
        writer.write(bytes([IAC, WILL, 1]) + b"R1> ")
        await writer.drain()
        # Read (ignoring telnet negotiation bytes) until the command line arrives.
        buf = bytearray()
        while b"show ip" not in bytes(buf):
            chunk = await reader.read(100)
            if not chunk:
                break
            buf += chunk
        received.append(bytes(buf))
        writer.write(b"PC1 : 10.0.0.1/24\r\n")
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    async with server:
        async with ConsoleSession("127.0.0.1", port, timeout=3.0) as sess:
            prompt = await sess.read_until_quiet(idle=0.2, max_wait=2.0)
            assert "R1>" in prompt
            await sess.send("show ip")
            out = await sess.read_until_quiet(idle=0.2, max_wait=2.0)
    assert "10.0.0.1/24" in clean_output(out)
    assert b"show ip" in received[0]
