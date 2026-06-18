"""Resource pool tools: group projects/templates/computes for RBAC scoping."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def pools_list(limit: int | None = None) -> list[dict[str, Any]]:
        """List resource pools."""
        return await client().list("/pools", limit=limit)

    @mcp.tool
    async def pool_get(pool_id: str) -> dict[str, Any]:
        """Get a resource pool."""
        return await client().get(f"/pools/{pool_id}")

    @mcp.tool
    async def pool_resources(pool_id: str) -> list[dict[str, Any]]:
        """List the resources contained in a pool."""
        return await client().get(f"/pools/{pool_id}/resources")

    if read_only():
        return

    @mcp.tool
    async def pool_create(name: str) -> dict[str, Any]:
        """Create a resource pool."""
        return await client().post("/pools", json={"name": name})

    @mcp.tool
    async def pool_update(pool_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update a resource pool (e.g. rename)."""
        return await client().put(f"/pools/{pool_id}", json=updates)

    @mcp.tool
    async def pool_delete(pool_id: str) -> str:
        """Delete a resource pool."""
        await client().delete(f"/pools/{pool_id}", parse=False)
        return f"Pool {pool_id} deleted."

    @mcp.tool
    async def pool_resource_add(pool_id: str, resource_id: str) -> str:
        """Add a resource (project/template/compute id) to a pool."""
        await client().put(f"/pools/{pool_id}/resources/{resource_id}", parse=False)
        return f"Resource {resource_id} added to pool {pool_id}."

    @mcp.tool
    async def pool_resource_remove(pool_id: str, resource_id: str) -> str:
        """Remove a resource from a pool."""
        await client().delete(f"/pools/{pool_id}/resources/{resource_id}", parse=False)
        return f"Resource {resource_id} removed from pool {pool_id}."
