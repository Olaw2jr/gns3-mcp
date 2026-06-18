"""Snapshot tools: list, create, delete, restore project snapshots."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client, resolve_project


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def snapshots_list(
        project_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """List snapshots of a project."""
        pid = resolve_project(project_id)
        return await client().list(f"/projects/{pid}/snapshots", limit=limit)

    if read_only():
        return

    @mcp.tool
    async def snapshot_create(name: str, project_id: str | None = None) -> dict[str, Any]:
        """Create a snapshot of the current project state."""
        pid = resolve_project(project_id)
        return await client().post(f"/projects/{pid}/snapshots", json={"name": name})

    @mcp.tool
    async def snapshot_restore(snapshot_id: str, project_id: str | None = None) -> dict[str, Any]:
        """Restore the project to a snapshot. The current state is overwritten."""
        pid = resolve_project(project_id)
        return await client().post(f"/projects/{pid}/snapshots/{snapshot_id}/restore")

    @mcp.tool
    async def snapshot_delete(snapshot_id: str, project_id: str | None = None) -> str:
        """Delete a snapshot."""
        pid = resolve_project(project_id)
        await client().delete(f"/projects/{pid}/snapshots/{snapshot_id}", parse=False)
        return f"Snapshot {snapshot_id} deleted."
