"""Opt-in live smoke test against a real GNS3 v3 controller.

Enable with GNS3_LIVE=1 and the usual GNS3_BASE_URL/GNS3_USERNAME/GNS3_PASSWORD env vars.
It exercises auth, project/node/link lifecycle, and console automation end-to-end, then
cleans everything up. Skipped by default so the unit suite stays hermetic.

    GNS3_LIVE=1 GNS3_BASE_URL=http://localhost:3080 \
    GNS3_USERNAME=admin GNS3_PASSWORD=... python -m pytest tests/test_live_smoke.py -s
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("GNS3_LIVE") != "1", reason="set GNS3_LIVE=1 to run the live smoke test"
)


@pytest.mark.asyncio
async def test_live_build_and_console():
    import gns3_mcp.runtime as runtime

    runtime._client = None
    runtime._settings = None
    from gns3_mcp.server import build_server

    mcp = build_server()
    tools = await mcp.get_tools()

    async def call(name, **kw):
        return await tools[name].fn(**kw)

    assert (await call("gns3_version"))["version"].startswith("3")

    # Find a VPCS template (always available, no images needed).
    templates = await call("templates_list")
    vpcs = next(t for t in templates if t["name"].lower() == "vpcs")

    project = await call("project_create", name="mcp-smoke")
    pid = project["project_id"]
    try:
        await call("project_open", project_id=pid)
        n1 = await call("node_create_from_template", template_id=vpcs["template_id"],
                        x=0, y=0, project_id=pid)
        n2 = await call("node_create_from_template", template_id=vpcs["template_id"],
                        x=200, y=0, project_id=pid)
        await call("link_create", node_a=n1["node_id"], adapter_a=0, port_a=0,
                   node_b=n2["node_id"], adapter_b=0, port_b=0, project_id=pid)
        await call("nodes_start_all", project_id=pid)

        # Configure an IP on PC1 via the console and read it back.
        await call("node_console_session", node_id=n1["node_id"], project_id=pid,
                   commands=["ip 10.0.0.1/24"])
        out = await call("node_console_send", node_id=n1["node_id"], project_id=pid,
                         command="show ip")
        assert "10.0.0.1" in out

        snap = await call("snapshot_create", name="smoke", project_id=pid)
        assert snap.get("snapshot_id")
        await call("nodes_stop_all", project_id=pid)
    finally:
        await call("project_delete", project_id=pid, confirm=True)
