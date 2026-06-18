"""Compute tools: manage GNS3 compute servers and query their emulators."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client


def _trim_compute(c: dict[str, Any]) -> dict[str, Any]:
    keep = ("compute_id", "name", "protocol", "host", "port", "connected", "cpu_usage_percent",
            "memory_usage_percent", "capabilities")
    return {k: c[k] for k in keep if k in c}


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def computes_list(limit: int | None = None) -> list[dict[str, Any]]:
        """List compute servers (id, name, host, connected state, load)."""
        items = await client().list("/computes", limit=limit)
        return [_trim_compute(c) for c in items]

    @mcp.tool
    async def compute_get(compute_id: str) -> dict[str, Any]:
        """Get full details for a compute server."""
        return await client().get(f"/computes/{compute_id}")

    @mcp.tool
    async def compute_emulator_query(
        compute_id: str, emulator: str, action: str
    ) -> Any:
        """Query an emulator on a compute, e.g. emulator='docker' action='images',
        emulator='virtualbox' action='vms', emulator='vmware' action='vms'."""
        return await client().get(f"/computes/{compute_id}/{emulator}/{action}")

    if read_only():
        return

    @mcp.tool
    async def compute_create(compute: dict[str, Any]) -> dict[str, Any]:
        """Register a compute server. `compute` needs protocol/host/port/name (+ auth)."""
        return _trim_compute(await client().post("/computes", json=compute))

    @mcp.tool
    async def compute_update(compute_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update a compute server's connection settings."""
        return _trim_compute(await client().put(f"/computes/{compute_id}", json=updates))

    @mcp.tool
    async def compute_delete(compute_id: str) -> str:
        """Unregister a compute server."""
        await client().delete(f"/computes/{compute_id}", parse=False)
        return f"Compute {compute_id} removed."
