"""Project tools: CRUD, open/close/load, duplicate, export/import, lock, files."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client, resolve_project


def _trim_project(p: dict[str, Any]) -> dict[str, Any]:
    keep = ("project_id", "name", "status", "path", "filename", "auto_open", "auto_start")
    return {k: p[k] for k in keep if k in p}


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def projects_list(limit: int | None = None) -> list[dict[str, Any]]:
        """List all projects on the controller (id, name, status)."""
        items = await client().list("/projects", limit=limit)
        return [_trim_project(p) for p in items]

    @mcp.tool
    async def project_get(project_id: str | None = None) -> dict[str, Any]:
        """Get full details for a project."""
        pid = resolve_project(project_id)
        return await client().get(f"/projects/{pid}")

    @mcp.tool
    async def project_stats(project_id: str | None = None) -> dict[str, Any]:
        """Get node/link/drawing/snapshot counts for a project."""
        pid = resolve_project(project_id)
        return await client().get(f"/projects/{pid}/stats")

    @mcp.tool
    async def project_locked(project_id: str | None = None) -> bool:
        """Return whether the project is currently locked."""
        pid = resolve_project(project_id)
        return await client().get(f"/projects/{pid}/locked")

    if read_only():
        return

    @mcp.tool
    async def project_create(
        name: str,
        auto_open: bool = False,
        auto_start: bool = False,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new project. Optionally pin a specific project_id (UUID)."""
        body: dict[str, Any] = {"name": name, "auto_open": auto_open, "auto_start": auto_start}
        if project_id:
            body["project_id"] = project_id
        return _trim_project(await client().post("/projects", json=body))

    @mcp.tool
    async def project_update(
        project_id: str | None = None, updates: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Update project attributes (e.g. {"name": "...", "auto_start": true})."""
        pid = resolve_project(project_id)
        return _trim_project(await client().put(f"/projects/{pid}", json=updates or {}))

    @mcp.tool
    async def project_delete(project_id: str, confirm: bool = False) -> str:
        """Delete a project permanently. Requires confirm=true. Destructive."""
        if not confirm:
            return "Refusing to delete project without confirm=true."
        await client().delete(f"/projects/{project_id}", parse=False)
        return f"Project {project_id} deleted."

    @mcp.tool
    async def project_open(project_id: str | None = None) -> dict[str, Any]:
        """Open a closed project so its nodes can run."""
        pid = resolve_project(project_id)
        return _trim_project(await client().post(f"/projects/{pid}/open"))

    @mcp.tool
    async def project_close(project_id: str | None = None) -> str:
        """Close an open project (stops nodes, frees resources)."""
        pid = resolve_project(project_id)
        await client().post(f"/projects/{pid}/close", parse=False)
        return f"Project {pid} closed."

    @mcp.tool
    async def project_load(path: str) -> dict[str, Any]:
        """Load a project from a .gns3 file path on the controller host."""
        return _trim_project(await client().post("/projects/load", json={"path": path}))

    @mcp.tool
    async def project_duplicate(
        project_id: str | None = None, name: str = "", reset_mac_addresses: bool = False
    ) -> dict[str, Any]:
        """Duplicate a project under a new name."""
        pid = resolve_project(project_id)
        body: dict[str, Any] = {"reset_mac_addresses": reset_mac_addresses}
        if name:
            body["name"] = name
        return _trim_project(await client().post(f"/projects/{pid}/duplicate", json=body))

    @mcp.tool
    async def project_lock(project_id: str | None = None) -> str:
        """Lock a project to prevent topology edits."""
        pid = resolve_project(project_id)
        await client().post(f"/projects/{pid}/lock", parse=False)
        return f"Project {pid} locked."

    @mcp.tool
    async def project_unlock(project_id: str | None = None) -> str:
        """Unlock a project."""
        pid = resolve_project(project_id)
        await client().post(f"/projects/{pid}/unlock", parse=False)
        return f"Project {pid} unlocked."

    @mcp.tool
    async def project_export(
        dest_path: str,
        project_id: str | None = None,
        include_images: bool = False,
        include_snapshots: bool = False,
        compression: str = "zstd",
    ) -> str:
        """Export a project to a local .gns3project archive at dest_path."""
        pid = resolve_project(project_id)
        params = {
            "include_images": str(include_images).lower(),
            "include_snapshots": str(include_snapshots).lower(),
            "compression": compression,
        }
        return await client().download(f"/projects/{pid}/export", dest_path, params=params)

    @mcp.tool
    async def project_import(src_path: str, name: str | None = None) -> dict[str, Any]:
        """Import a project from a local .gns3project archive."""
        params = {"name": name} if name else None
        from ..runtime import get_client

        # Import targets /projects/{new_id}/import; GNS3 also accepts a controller-side import
        # via the project id embedded in the archive — we use the generic upload endpoint.
        result = await get_client().upload("/projects/import", src_path)
        return _trim_project(result) if isinstance(result, dict) else {"params": params}

    @mcp.tool
    async def project_file_read(file_path: str, project_id: str | None = None) -> str:
        """Read a text file from inside the project directory."""
        pid = resolve_project(project_id)
        resp = await client().get(f"/projects/{pid}/files/{file_path}", parse=False)
        return resp.text

    @mcp.tool
    async def project_file_write(
        file_path: str, content: str, project_id: str | None = None
    ) -> str:
        """Write a text file inside the project directory."""
        pid = resolve_project(project_id)
        await client().send_content(
            "POST", f"/projects/{pid}/files/{file_path}", content.encode(), parse=False
        )
        return f"Wrote {file_path}."
