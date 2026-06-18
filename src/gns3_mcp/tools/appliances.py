"""Appliance tools: browse the GNS3 appliance catalog and install appliances."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def appliances_list(
        update: bool = False, symbol_theme: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """List appliances from the GNS3 catalog. Set update=true to refresh from registry."""
        params: dict[str, Any] = {}
        if update:
            params["update"] = "true"
        if symbol_theme:
            params["symbol_theme"] = symbol_theme
        items = await client().list("/appliances", params=params or None, limit=limit)
        return [
            {k: a[k] for k in ("appliance_id", "name", "category", "vendor_name", "status")
             if k in a}
            for a in items
        ]

    @mcp.tool
    async def appliance_get(appliance_id: str) -> dict[str, Any]:
        """Get full details for an appliance (versions, images required)."""
        return await client().get(f"/appliances/{appliance_id}")

    if read_only():
        return

    @mcp.tool
    async def appliance_install(
        appliance_id: str, version: str | None = None
    ) -> dict[str, Any]:
        """Install an appliance as a template (optionally a specific version)."""
        params = {"version": version} if version else None
        return await client().post(f"/appliances/{appliance_id}/install", params=params)
