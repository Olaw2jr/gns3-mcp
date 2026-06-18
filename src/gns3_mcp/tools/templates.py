"""Template tools: list, get, create, update, delete, duplicate device templates."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client


def _trim_template(t: dict[str, Any]) -> dict[str, Any]:
    keep = ("template_id", "name", "template_type", "category", "compute_id", "builtin")
    return {k: t[k] for k in keep if k in t}


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def templates_list(limit: int | None = None) -> list[dict[str, Any]]:
        """List device templates (id, name, type, category)."""
        items = await client().list("/templates", limit=limit)
        return [_trim_template(t) for t in items]

    @mcp.tool
    async def template_get(template_id: str) -> dict[str, Any]:
        """Get full details for a template (all properties)."""
        return await client().get(f"/templates/{template_id}")

    if read_only():
        return

    @mcp.tool
    async def template_create(template: dict[str, Any]) -> dict[str, Any]:
        """Create a template. `template` must include name and template_type plus props."""
        return _trim_template(await client().post("/templates", json=template))

    @mcp.tool
    async def template_update(template_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update a template's attributes."""
        return _trim_template(await client().put(f"/templates/{template_id}", json=updates))

    @mcp.tool
    async def template_delete(template_id: str) -> str:
        """Delete a template."""
        await client().delete(f"/templates/{template_id}", parse=False)
        return f"Template {template_id} deleted."

    @mcp.tool
    async def template_duplicate(template_id: str) -> dict[str, Any]:
        """Duplicate a template."""
        return _trim_template(await client().post(f"/templates/{template_id}/duplicate"))
