"""Console automation tools: type CLI commands into node consoles and read output.

These tools open a telnet connection to a node's console server (console_host:console)
for the duration of the call, send commands, and return the device output. They work
for telnet-type consoles (routers, switches, VPCS, most appliances). VNC/SPICE consoles
cannot be driven and are reported as connection info only.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..console import ConsoleSession, clean_output
from ..errors import GNS3Error
from ..runtime import get_runtime_settings, read_only
from ._common import client, resolve_project


async def _console_target(pid: str, node_id: str) -> tuple[str, int]:
    node = await client().get(f"/projects/{pid}/nodes/{node_id}")
    ctype = node.get("console_type")
    if ctype not in (None, "telnet"):
        raise GNS3Error(
            f"Node console_type is '{ctype}', not telnet — cannot drive it as text. "
            f"Use node_console_info for connection details."
        )
    if node.get("status") != "started":
        raise GNS3Error("Node is not started — start it before using the console.")
    host = node.get("console_host") or "127.0.0.1"
    if host in ("0.0.0.0", "::"):
        host = get_runtime_settings().base_url.split("://")[-1].split(":")[0].split("/")[0]
    port = node.get("console")
    if not port:
        raise GNS3Error("Node has no console port allocated.")
    return host, int(port)


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def node_console_info(node_id: str, project_id: str | None = None) -> dict[str, Any]:
        """Return console connection info for a node (host, port, type)."""
        pid = resolve_project(project_id)
        node = await client().get(f"/projects/{pid}/nodes/{node_id}")
        return {
            "name": node.get("name"),
            "status": node.get("status"),
            "console_type": node.get("console_type"),
            "console_host": node.get("console_host"),
            "console_port": node.get("console"),
        }

    if read_only():
        return

    @mcp.tool
    async def node_console_send(
        node_id: str,
        command: str,
        project_id: str | None = None,
        idle: float = 0.5,
        max_wait: float | None = None,
    ) -> str:
        """Send a single command to a node's telnet console and return the output.

        Reads until the console is idle for `idle` seconds (or `max_wait` total). Sends a
        blank line first to capture the current prompt.
        """
        pid = resolve_project(project_id)
        host, port = await _console_target(pid, node_id)
        timeout = max_wait or get_runtime_settings().console_timeout
        async with ConsoleSession(host, port, timeout) as sess:
            await sess.send("")  # nudge to get a prompt
            await sess.read_until_quiet(idle=idle, max_wait=2.0)
            await sess.send(command)
            out = await sess.read_until_quiet(idle=idle, max_wait=timeout)
        return clean_output(out)

    @mcp.tool
    async def node_console_session(
        node_id: str,
        commands: list[str],
        project_id: str | None = None,
        idle: float = 0.5,
        per_command_wait: float | None = None,
    ) -> list[dict[str, str]]:
        """Run a sequence of commands on a node console in one connection.

        Returns a list of {command, output} entries. Useful for entering config mode and
        applying several lines (e.g. ['enable', 'conf t', 'interface g0/0', 'ip address ...']).
        """
        pid = resolve_project(project_id)
        host, port = await _console_target(pid, node_id)
        timeout = per_command_wait or get_runtime_settings().console_timeout
        results: list[dict[str, str]] = []
        async with ConsoleSession(host, port, timeout) as sess:
            await sess.send("")
            await sess.read_until_quiet(idle=idle, max_wait=2.0)
            for cmd in commands:
                await sess.send(cmd)
                out = await sess.read_until_quiet(idle=idle, max_wait=timeout)
                results.append({"command": cmd, "output": clean_output(out)})
        return results

    @mcp.tool
    async def node_console_read(
        node_id: str,
        project_id: str | None = None,
        idle: float = 0.5,
        max_wait: float = 5.0,
    ) -> str:
        """Connect and drain any pending console output without sending a command."""
        pid = resolve_project(project_id)
        host, port = await _console_target(pid, node_id)
        async with ConsoleSession(host, port, max_wait) as sess:
            out = await sess.read_until_quiet(idle=idle, max_wait=max_wait)
        return clean_output(out)
