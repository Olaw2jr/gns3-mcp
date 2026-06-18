"""Shared helpers for tool modules."""

from __future__ import annotations

from typing import Any

from ..errors import GNS3Error
from ..runtime import get_client, get_runtime_settings


def client():
    return get_client()


def resolve_project(project_id: str | None) -> str:
    """Return the project id, falling back to GNS3_DEFAULT_PROJECT."""
    pid = project_id or get_runtime_settings().default_project
    if not pid:
        raise GNS3Error(
            "No project_id given and GNS3_DEFAULT_PROJECT is not set."
        )
    return pid


# Fields that are verbose and rarely useful in an LLM context window.
_NOISY = {"x", "y", "z", "width", "height", "symbol", "label", "properties_schema"}


def trim_node(node: dict[str, Any]) -> dict[str, Any]:
    """Return a node dict reduced to the fields that matter for reasoning."""
    keep = (
        "node_id",
        "name",
        "node_type",
        "status",
        "console",
        "console_type",
        "console_host",
        "compute_id",
        "project_id",
        "template_id",
        "ports",
    )
    out = {k: node[k] for k in keep if k in node}
    # Reduce port objects to the essentials.
    if isinstance(out.get("ports"), list):
        out["ports"] = [
            {
                "name": p.get("name"),
                "short_name": p.get("short_name"),
                "adapter_number": p.get("adapter_number"),
                "port_number": p.get("port_number"),
                "link_type": p.get("link_type"),
            }
            for p in out["ports"]
        ]
    return out


def trim_link(link: dict[str, Any]) -> dict[str, Any]:
    keep = ("link_id", "link_type", "suspend", "filters", "capturing", "capture_file_name")
    out = {k: link[k] for k in keep if k in link}
    nodes = link.get("nodes") or []
    out["nodes"] = [
        {
            "node_id": n.get("node_id"),
            "adapter_number": n.get("adapter_number"),
            "port_number": n.get("port_number"),
        }
        for n in nodes
    ]
    return out
