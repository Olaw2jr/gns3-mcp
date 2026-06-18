"""End-to-end tool tests: tool function -> GNS3Client -> mocked HTTP.

Tools are invoked via their underlying ``.fn`` (the registered coroutine) rather than the
FastMCP in-memory Client, which keeps the test focused on our code and avoids unrelated
server-transport plumbing.
"""

import json

import httpx
import pytest
import respx

BASE = "http://gns3.test:3080"
API = BASE + "/v3"


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("GNS3_BASE_URL", BASE)
    monkeypatch.setenv("GNS3_USERNAME", "admin")
    monkeypatch.setenv("GNS3_PASSWORD", "secret")
    monkeypatch.delenv("GNS3_READ_ONLY", raising=False)
    monkeypatch.delenv("GNS3_TOKEN", raising=False)


async def get_tools(read_only=False, monkeypatch=None):
    import inspect

    import gns3_mcp.runtime as runtime

    runtime._client = None
    runtime._settings = None
    from gns3_mcp.server import build_server

    mcp = build_server()
    # Resolve the registered tools across FastMCP versions: prefer the public
    # get_tools() accessor, fall back to the ToolManager's tool dict.
    getter = getattr(mcp, "get_tools", None)
    if callable(getter):
        result = getter()
        return await result if inspect.isawaitable(result) else result
    return mcp._tool_manager._tools


async def call(tools, name, **kwargs):
    return await tools[name].fn(**kwargs)


@pytest.mark.asyncio
@respx.mock
async def test_gns3_version_tool(env):
    respx.post(f"{API}/access/users/login").mock(
        return_value=httpx.Response(200, json={"access_token": "T"})
    )
    respx.get(f"{API}/version").mock(
        return_value=httpx.Response(200, json={"version": "3.0.0", "local": True})
    )
    tools = await get_tools()
    out = await call(tools, "gns3_version")
    assert out["version"] == "3.0.0"


@pytest.mark.asyncio
@respx.mock
async def test_node_create_from_template_posts_right_path(env):
    respx.post(f"{API}/access/users/login").mock(
        return_value=httpx.Response(200, json={"access_token": "T"})
    )
    route = respx.post(f"{API}/projects/proj1/templates/tmpl1").mock(
        return_value=httpx.Response(
            201,
            json={"node_id": "n1", "name": "R1", "node_type": "qemu", "status": "stopped"},
        )
    )
    tools = await get_tools()
    out = await call(
        tools, "node_create_from_template",
        template_id="tmpl1", x=10, y=20, project_id="proj1",
    )
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["x"] == 10 and body["y"] == 20
    assert out["node_id"] == "n1"
    # trimmed output shouldn't leak verbose fields
    assert "properties" not in out


@pytest.mark.asyncio
@respx.mock
async def test_link_create_builds_endpoint_payload(env):
    respx.post(f"{API}/access/users/login").mock(
        return_value=httpx.Response(200, json={"access_token": "T"})
    )
    route = respx.post(f"{API}/projects/proj1/links").mock(
        return_value=httpx.Response(201, json={"link_id": "l1", "nodes": []})
    )
    tools = await get_tools()
    await call(
        tools, "link_create",
        node_a="na", adapter_a=0, port_a=0,
        node_b="nb", adapter_b=0, port_b=1, project_id="proj1",
    )
    body = json.loads(route.calls.last.request.content)
    assert body["nodes"][0]["node_id"] == "na"
    assert body["nodes"][1]["port_number"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_project_delete_requires_confirm(env):
    respx.post(f"{API}/access/users/login").mock(
        return_value=httpx.Response(200, json={"access_token": "T"})
    )
    delete_route = respx.delete(f"{API}/projects/p1").mock(return_value=httpx.Response(204))
    tools = await get_tools()
    res = await call(tools, "project_delete", project_id="p1", confirm=False)
    assert "confirm=true" in res
    assert not delete_route.called
    await call(tools, "project_delete", project_id="p1", confirm=True)
    assert delete_route.called


@pytest.mark.asyncio
async def test_read_only_hides_mutating_tools(env, monkeypatch):
    monkeypatch.setenv("GNS3_READ_ONLY", "true")
    tools = await get_tools()
    assert "gns3_version" in tools
    assert "projects_list" in tools
    for muting in ("node_create", "project_delete", "link_create", "user_create"):
        assert muting not in tools


@pytest.mark.asyncio
@respx.mock
async def test_nodes_list_is_trimmed(env):
    respx.post(f"{API}/access/users/login").mock(
        return_value=httpx.Response(200, json={"access_token": "T"})
    )
    respx.get(f"{API}/projects/p1/nodes").mock(
        return_value=httpx.Response(
            200,
            json=[{
                "node_id": "n1", "name": "R1", "node_type": "qemu", "status": "started",
                "console": 5000, "x": -123, "y": 456, "symbol": ":/symbols/router.svg",
                "properties": {"ram": 512},
            }],
        )
    )
    tools = await get_tools()
    out = await call(tools, "nodes_list", project_id="p1")
    assert out[0]["name"] == "R1"
    assert "x" not in out[0] and "symbol" not in out[0] and "properties" not in out[0]
