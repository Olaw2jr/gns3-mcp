"""Controller-level tools: version, statistics, admin, IOU license."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def gns3_version() -> dict[str, Any]:
        """Return the GNS3 controller version and whether it runs in local mode."""
        return await client().get("/version")

    @mcp.tool
    async def gns3_statistics() -> dict[str, Any]:
        """Return controller-wide statistics (counts of projects, computes, etc.)."""
        return await client().get("/statistics")

    @mcp.tool
    async def iou_license_get() -> dict[str, Any]:
        """Return the configured Cisco IOU license (if any)."""
        return await client().get("/iou_license")

    if read_only():
        return

    @mcp.tool
    async def iou_license_set(iourc_content: str, license_check: bool = True) -> dict[str, Any]:
        """Set the Cisco IOU license. iourc_content is the raw iourc file text."""
        return await client().put(
            "/iou_license",
            json={"iourc_content": iourc_content, "license_check": license_check},
        )

    @mcp.tool
    async def controller_reload(confirm: bool = False) -> str:
        """Reload the GNS3 controller. Requires confirm=true."""
        if not confirm:
            return "Refusing to reload controller without confirm=true."
        await client().post("/reload", parse=False)
        return "Controller reload requested."

    @mcp.tool
    async def controller_shutdown(confirm: bool = False) -> str:
        """Shut down the GNS3 controller process. Requires confirm=true. Destructive."""
        if not confirm:
            return "Refusing to shut down controller without confirm=true."
        await client().post("/shutdown", parse=False)
        return "Controller shutdown requested."
