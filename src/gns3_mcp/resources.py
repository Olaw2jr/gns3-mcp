"""MCP resources (read-only context) and prompts (reusable workflows)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from .tools._common import client, trim_link, trim_node


def register(mcp: FastMCP) -> None:
    # ------------------------------------------------------------ resources
    @mcp.resource("gns3://projects")
    async def projects_resource() -> list[dict[str, Any]]:
        """All projects on the controller."""
        items = await client().list("/projects")
        return [
            {k: p[k] for k in ("project_id", "name", "status") if k in p} for p in items
        ]

    @mcp.resource("gns3://templates")
    async def templates_resource() -> list[dict[str, Any]]:
        """All device templates."""
        items = await client().list("/templates")
        return [
            {k: t[k] for k in ("template_id", "name", "template_type", "category") if k in t}
            for t in items
        ]

    @mcp.resource("gns3://computes")
    async def computes_resource() -> list[dict[str, Any]]:
        """All compute servers."""
        return await client().list("/computes")

    @mcp.resource("gns3://project/{project_id}/topology")
    async def topology_resource(project_id: str) -> dict[str, Any]:
        """A project's full topology: nodes, links, and drawings in one document."""
        nodes = await client().list(f"/projects/{project_id}/nodes")
        links = await client().list(f"/projects/{project_id}/links")
        drawings = await client().list(f"/projects/{project_id}/drawings")
        return {
            "project_id": project_id,
            "nodes": [trim_node(n) for n in nodes],
            "links": [trim_link(link) for link in links],
            "drawings": len(drawings),
        }

    # -------------------------------------------------------------- prompts
    @mcp.prompt
    def build_lab(description: str) -> str:
        """Guide building a GNS3 lab topology from a natural-language description."""
        return (
            f"Build a GNS3 lab for: {description}\n\n"
            "Steps:\n"
            "1. Call templates_list to see available device templates.\n"
            "2. Create a project (project_create) and open it (project_open).\n"
            "3. Add nodes with node_create_from_template, spacing them on the canvas (x,y).\n"
            "4. Inspect each node's ports (node_get) and connect them with link_create.\n"
            "5. Start nodes (nodes_start_all) and verify with node_console_send.\n"
            "Confirm the topology with the gns3://project/<id>/topology resource."
        )

    @mcp.prompt
    def troubleshoot_node(node_id: str, symptom: str) -> str:
        """Guide troubleshooting a misbehaving node."""
        return (
            f"Troubleshoot node {node_id} with symptom: {symptom}\n\n"
            "1. node_get to confirm status/console_type.\n"
            "2. If not started, node_start; otherwise node_console_send diagnostic commands "
            "(e.g. 'show ip interface brief', 'show running-config').\n"
            "3. Inspect links with node_links and consider capture_start to observe traffic.\n"
            "4. Propose and apply a fix via node_console_session, then re-verify."
        )

    @mcp.prompt
    def snapshot_before_change(project_id: str, change: str) -> str:
        """Remind to snapshot before a risky change and how to roll back."""
        return (
            f"Before applying '{change}' to project {project_id}:\n"
            "1. snapshot_create(name='before-<change>').\n"
            "2. Apply the change.\n"
            "3. If it regresses, snapshot_restore to roll back; otherwise keep going."
        )
