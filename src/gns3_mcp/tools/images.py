"""Image tools: list, upload, install, delete, prune disk images."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..runtime import read_only
from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def images_list(limit: int | None = None) -> list[dict[str, Any]]:
        """List disk images known to the controller (qemu/ios/iou/docker)."""
        return await client().list("/images", limit=limit)

    @mcp.tool
    async def image_get(image_path: str) -> dict[str, Any]:
        """Get metadata for an image by its path."""
        return await client().get(f"/images/{image_path}")

    if read_only():
        return

    @mcp.tool
    async def image_upload(image_path: str, src_path: str) -> dict[str, Any]:
        """Upload a local image file to the controller under image_path."""
        return await client().upload(f"/images/upload/{image_path}", src_path)

    @mcp.tool
    async def image_install(image_path: str | None = None) -> Any:
        """Install/register images so templates can use them (optionally one path)."""
        body = {"image_path": image_path} if image_path else None
        return await client().post("/images/install", json=body)

    @mcp.tool
    async def image_delete(image_path: str) -> str:
        """Delete an image by path."""
        await client().delete(f"/images/{image_path}", parse=False)
        return f"Image {image_path} deleted."

    @mcp.tool
    async def images_prune(confirm: bool = False) -> str:
        """Delete all images not used by any template. Requires confirm=true."""
        if not confirm:
            return "Refusing to prune images without confirm=true."
        await client().delete("/images/prune", parse=False)
        return "Unused images pruned."
