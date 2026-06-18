"""Link tools: CRUD, filters, reset, and packet capture control."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client, resolve_project, trim_link


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def links_list(
        project_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """List links in a project (id, endpoints, capture state, filters)."""
        pid = resolve_project(project_id)
        items = await client().list(f"/projects/{pid}/links", limit=limit)
        return [trim_link(link) for link in items]

    @mcp.tool
    async def link_get(link_id: str, project_id: str | None = None) -> dict[str, Any]:
        """Get full details for a link."""
        pid = resolve_project(project_id)
        return await client().get(f"/projects/{pid}/links/{link_id}")

    @mcp.tool
    async def link_available_filters(
        link_id: str, project_id: str | None = None
    ) -> list[dict[str, Any]]:
        """List packet filters available on a link (delay, drop, corrupt, etc.)."""
        pid = resolve_project(project_id)
        return await client().get(f"/projects/{pid}/links/{link_id}/available_filters")

    if read_only():
        return

    @mcp.tool
    async def link_create(
        node_a: str,
        adapter_a: int,
        port_a: int,
        node_b: str,
        adapter_b: int,
        port_b: int,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a link between two node ports.

        Use a node's `ports` (from node_get/nodes_list) to find adapter_number/port_number.
        """
        pid = resolve_project(project_id)
        body = {
            "nodes": [
                {"node_id": node_a, "adapter_number": adapter_a, "port_number": port_a},
                {"node_id": node_b, "adapter_number": adapter_b, "port_number": port_b},
            ]
        }
        return trim_link(await client().post(f"/projects/{pid}/links", json=body))

    @mcp.tool
    async def link_update(
        link_id: str, updates: dict[str, Any], project_id: str | None = None
    ) -> dict[str, Any]:
        """Update a link: set {"suspend": true} or {"filters": {"delay": [50]}} etc."""
        pid = resolve_project(project_id)
        return trim_link(await client().put(f"/projects/{pid}/links/{link_id}", json=updates))

    @mcp.tool
    async def link_delete(link_id: str, project_id: str | None = None) -> str:
        """Delete a link."""
        pid = resolve_project(project_id)
        await client().delete(f"/projects/{pid}/links/{link_id}", parse=False)
        return f"Link {link_id} deleted."

    @mcp.tool
    async def link_reset(link_id: str, project_id: str | None = None) -> str:
        """Reset a link (reconnect both ends)."""
        pid = resolve_project(project_id)
        await client().post(f"/projects/{pid}/links/{link_id}/reset", parse=False)
        return f"Link {link_id} reset."
