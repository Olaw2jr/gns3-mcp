"""Packet capture tools: start/stop captures on links and download pcap files."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client, resolve_project


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def capture_download(
        link_id: str, dest_path: str, project_id: str | None = None
    ) -> str:
        """Download the current/last pcap capture file for a link to dest_path."""
        pid = resolve_project(project_id)
        return await client().download(
            f"/projects/{pid}/links/{link_id}/capture/file", dest_path
        )

    if read_only():
        return

    @mcp.tool
    async def capture_start(
        link_id: str,
        data_link_type: str = "DLT_EN10MB",
        capture_file_name: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a packet capture on a link (DLT_EN10MB for Ethernet)."""
        pid = resolve_project(project_id)
        body: dict[str, Any] = {"data_link_type": data_link_type}
        if capture_file_name:
            body["capture_file_name"] = capture_file_name
        return await client().post(
            f"/projects/{pid}/links/{link_id}/capture/start", json=body
        )

    @mcp.tool
    async def capture_stop(link_id: str, project_id: str | None = None) -> str:
        """Stop the packet capture on a link."""
        pid = resolve_project(project_id)
        await client().post(f"/projects/{pid}/links/{link_id}/capture/stop", parse=False)
        return f"Capture stopped on link {link_id}."

    @mcp.tool
    async def capture_wireshark_restart(link_id: str, project_id: str | None = None) -> str:
        """Restart the live Wireshark capture stream on a link."""
        pid = resolve_project(project_id)
        await client().post(
            f"/projects/{pid}/links/{link_id}/capture/wireshark/restart", parse=False
        )
        return f"Wireshark capture restarted on link {link_id}."
