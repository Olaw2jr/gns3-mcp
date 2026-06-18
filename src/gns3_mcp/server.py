"""FastMCP server entry point for the GNS3 v3 controller.

Registers every tool module, MCP resources, and prompts, then runs the selected
transport (stdio by default, streamable-HTTP when GNS3_TRANSPORT=http).
"""

from __future__ import annotations

from fastmcp import FastMCP

from . import resources
from .runtime import init_runtime
from .tools import (
    access,
    appliances,
    capture,
    computes,
    console,
    controller,
    drawings,
    images,
    links,
    nodes,
    pools,
    projects,
    snapshots,
    templates,
)

_TOOL_MODULES = [
    controller,
    projects,
    nodes,
    links,
    drawings,
    snapshots,
    templates,
    computes,
    images,
    appliances,
    pools,
    access,
    console,
    capture,
]


def build_server() -> FastMCP:
    """Construct the FastMCP app with runtime initialised and all modules registered."""
    settings = init_runtime()
    mcp = FastMCP(
        name="gns3",
        instructions=(
            "Tools to drive a GNS3 v3 network-emulation controller: build topologies "
            "(projects, nodes, links), manage device lifecycle, snapshot, capture packets, "
            "manage templates/computes/images/RBAC, and automate device CLIs over node "
            "consoles. Open a project with project_open before manipulating its nodes."
        ),
    )
    for module in _TOOL_MODULES:
        module.register(mcp)
    resources.register(mcp)

    if settings.read_only:
        mcp.instructions += " (Server is in READ-ONLY mode; mutating tools are disabled.)"
    return mcp


def main() -> None:
    """Console-script entry point."""
    from .runtime import get_runtime_settings

    mcp = build_server()
    settings = get_runtime_settings()
    if settings.transport == "http":
        mcp.run(transport="http", host=settings.http_host, port=settings.http_port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
