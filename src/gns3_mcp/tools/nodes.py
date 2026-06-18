"""Node tools: CRUD, instantiate-from-template, lifecycle, isolate, files, disks."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client, resolve_project, trim_node


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def nodes_list(
        project_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """List nodes in a project (id, name, type, status, console)."""
        pid = resolve_project(project_id)
        items = await client().list(f"/projects/{pid}/nodes", limit=limit)
        return [trim_node(n) for n in items]

    @mcp.tool
    async def node_get(node_id: str, project_id: str | None = None) -> dict[str, Any]:
        """Get full details for a single node."""
        pid = resolve_project(project_id)
        return await client().get(f"/projects/{pid}/nodes/{node_id}")

    @mcp.tool
    async def node_links(node_id: str, project_id: str | None = None) -> list[dict[str, Any]]:
        """List the links attached to a node."""
        pid = resolve_project(project_id)
        return await client().get(f"/projects/{pid}/nodes/{node_id}/links")

    @mcp.tool
    async def node_idlepc_proposals(
        node_id: str, project_id: str | None = None
    ) -> list[str]:
        """Get Dynamips idle-PC proposals for a node."""
        pid = resolve_project(project_id)
        return await client().get(
            f"/projects/{pid}/nodes/{node_id}/dynamips/idlepc_proposals"
        )

    if read_only():
        return

    @mcp.tool
    async def node_create(
        name: str,
        node_type: str,
        compute_id: str = "local",
        properties: dict[str, Any] | None = None,
        console_type: str | None = None,
        x: int = 0,
        y: int = 0,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a node directly (node_type e.g. vpcs, qemu, docker, dynamips, ethernet_switch).

        Prefer node_create_from_template when a suitable template exists.
        """
        pid = resolve_project(project_id)
        body: dict[str, Any] = {
            "name": name,
            "node_type": node_type,
            "compute_id": compute_id,
            "x": x,
            "y": y,
        }
        if properties:
            body["properties"] = properties
        if console_type:
            body["console_type"] = console_type
        return trim_node(await client().post(f"/projects/{pid}/nodes", json=body))

    @mcp.tool
    async def node_create_from_template(
        template_id: str,
        x: int = 0,
        y: int = 0,
        name: str | None = None,
        compute_id: str = "local",
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Instantiate a node from a template at canvas position (x, y)."""
        pid = resolve_project(project_id)
        body: dict[str, Any] = {"x": x, "y": y, "compute_id": compute_id}
        if name:
            body["name"] = name
        return trim_node(
            await client().post(f"/projects/{pid}/templates/{template_id}", json=body)
        )

    @mcp.tool
    async def node_update(
        node_id: str, updates: dict[str, Any], project_id: str | None = None
    ) -> dict[str, Any]:
        """Update node attributes (e.g. {"name": "...", "properties": {...}})."""
        pid = resolve_project(project_id)
        return trim_node(await client().put(f"/projects/{pid}/nodes/{node_id}", json=updates))

    @mcp.tool
    async def node_delete(node_id: str, project_id: str | None = None) -> str:
        """Delete a node from the project."""
        pid = resolve_project(project_id)
        await client().delete(f"/projects/{pid}/nodes/{node_id}", parse=False)
        return f"Node {node_id} deleted."

    @mcp.tool
    async def node_duplicate(
        node_id: str, dx: int = 10, dy: int = 10, project_id: str | None = None
    ) -> dict[str, Any]:
        """Duplicate a node, offset by (dx, dy) on the canvas."""
        pid = resolve_project(project_id)
        return trim_node(
            await client().post(
                f"/projects/{pid}/nodes/{node_id}/duplicate",
                json={"x": dx, "y": dy, "z": 0},
            )
        )

    # --- lifecycle (single node) ---
    async def _action(node_id: str, project_id: str | None, action: str) -> str:
        pid = resolve_project(project_id)
        await client().post(f"/projects/{pid}/nodes/{node_id}/{action}", parse=False)
        return f"Node {node_id}: {action} requested."

    @mcp.tool
    async def node_start(node_id: str, project_id: str | None = None) -> str:
        """Start a node."""
        return await _action(node_id, project_id, "start")

    @mcp.tool
    async def node_stop(node_id: str, project_id: str | None = None) -> str:
        """Stop a node."""
        return await _action(node_id, project_id, "stop")

    @mcp.tool
    async def node_suspend(node_id: str, project_id: str | None = None) -> str:
        """Suspend a node."""
        return await _action(node_id, project_id, "suspend")

    @mcp.tool
    async def node_reload(node_id: str, project_id: str | None = None) -> str:
        """Reload (restart) a node."""
        return await _action(node_id, project_id, "reload")

    @mcp.tool
    async def node_isolate(node_id: str, project_id: str | None = None) -> str:
        """Isolate a node: suspend all its links (cut traffic without deleting links)."""
        return await _action(node_id, project_id, "isolate")

    @mcp.tool
    async def node_unisolate(node_id: str, project_id: str | None = None) -> str:
        """Re-enable all links on a previously isolated node."""
        return await _action(node_id, project_id, "unisolate")

    @mcp.tool
    async def node_console_reset(node_id: str, project_id: str | None = None) -> str:
        """Reset the console server connection for a node."""
        return await _action(node_id, project_id, "console/reset")

    # --- lifecycle (all nodes) ---
    @mcp.tool
    async def nodes_start_all(project_id: str | None = None) -> str:
        """Start every node in the project."""
        pid = resolve_project(project_id)
        await client().post(f"/projects/{pid}/nodes/start", parse=False)
        return "Start-all requested."

    @mcp.tool
    async def nodes_stop_all(project_id: str | None = None) -> str:
        """Stop every node in the project."""
        pid = resolve_project(project_id)
        await client().post(f"/projects/{pid}/nodes/stop", parse=False)
        return "Stop-all requested."

    @mcp.tool
    async def nodes_suspend_all(project_id: str | None = None) -> str:
        """Suspend every node in the project."""
        pid = resolve_project(project_id)
        await client().post(f"/projects/{pid}/nodes/suspend", parse=False)
        return "Suspend-all requested."

    @mcp.tool
    async def nodes_reload_all(project_id: str | None = None) -> str:
        """Reload every node in the project."""
        pid = resolve_project(project_id)
        await client().post(f"/projects/{pid}/nodes/reload", parse=False)
        return "Reload-all requested."

    @mcp.tool
    async def node_idlepc_auto(node_id: str, project_id: str | None = None) -> dict[str, Any]:
        """Auto-compute a Dynamips idle-PC value for a node."""
        pid = resolve_project(project_id)
        return await client().get(f"/projects/{pid}/nodes/{node_id}/dynamips/auto_idlepc")

    @mcp.tool
    async def node_file_read(
        node_id: str, file_path: str, project_id: str | None = None
    ) -> str:
        """Read a text file from inside a node's working directory."""
        pid = resolve_project(project_id)
        resp = await client().get(
            f"/projects/{pid}/nodes/{node_id}/files/{file_path}", parse=False
        )
        return resp.text

    @mcp.tool
    async def node_file_write(
        node_id: str, file_path: str, content: str, project_id: str | None = None
    ) -> str:
        """Write a text file into a node's working directory (e.g. startup-config)."""
        pid = resolve_project(project_id)
        await client().send_content(
            "POST",
            f"/projects/{pid}/nodes/{node_id}/files/{file_path}",
            content.encode(),
            parse=False,
        )
        return f"Wrote {file_path} on node {node_id}."
