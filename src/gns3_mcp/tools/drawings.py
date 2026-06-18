"""Drawing tools: canvas annotations (rectangles, ellipses, text, lines as SVG)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client, resolve_project


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def drawings_list(
        project_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """List drawings (SVG annotations) in a project."""
        pid = resolve_project(project_id)
        return await client().list(f"/projects/{pid}/drawings", limit=limit)

    if read_only():
        return

    @mcp.tool
    async def drawing_create(
        svg: str, x: int = 0, y: int = 0, z: int = 1, project_id: str | None = None
    ) -> dict[str, Any]:
        """Create a drawing from an SVG string at canvas position (x, y)."""
        pid = resolve_project(project_id)
        return await client().post(
            f"/projects/{pid}/drawings", json={"svg": svg, "x": x, "y": y, "z": z}
        )

    @mcp.tool
    async def drawing_update(
        drawing_id: str, updates: dict[str, Any], project_id: str | None = None
    ) -> dict[str, Any]:
        """Update a drawing (svg/x/y/z/rotation)."""
        pid = resolve_project(project_id)
        return await client().put(f"/projects/{pid}/drawings/{drawing_id}", json=updates)

    @mcp.tool
    async def drawing_delete(drawing_id: str, project_id: str | None = None) -> str:
        """Delete a drawing."""
        pid = resolve_project(project_id)
        await client().delete(f"/projects/{pid}/drawings/{drawing_id}", parse=False)
        return f"Drawing {drawing_id} deleted."
