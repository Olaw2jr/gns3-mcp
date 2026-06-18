import httpx
import pytest
import respx

from gns3_mcp.client import GNS3Client
from gns3_mcp.config import Settings
from gns3_mcp.errors import GNS3Error

BASE = "http://gns3.test:3080"
API = BASE + "/v3"


def make_client(**kw):
    settings = Settings(
        base_url=BASE, username="admin", password="secret", **kw
    )
    return GNS3Client(settings)


@pytest.mark.asyncio
@respx.mock
async def test_login_and_request_attaches_bearer():
    login = respx.post(f"{API}/access/users/login").mock(
        return_value=httpx.Response(200, json={"access_token": "TOK"})
    )
    ver = respx.get(f"{API}/version").mock(
        return_value=httpx.Response(200, json={"version": "3.0.0"})
    )
    client = make_client()
    out = await client.get("/version")
    assert out == {"version": "3.0.0"}
    assert login.called
    # form-encoded credentials
    assert b"username=admin" in login.calls.last.request.content
    # bearer header attached to the data request
    assert ver.calls.last.request.headers["authorization"] == "Bearer TOK"
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_token_setting_skips_login():
    ver = respx.get(f"{API}/version").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    client = make_client(token="PRESET")
    await client.get("/version")
    assert ver.calls.last.request.headers["authorization"] == "Bearer PRESET"
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_reauth_on_401():
    respx.post(f"{API}/access/users/login").mock(
        side_effect=[
            httpx.Response(200, json={"access_token": "OLD"}),
            httpx.Response(200, json={"access_token": "NEW"}),
        ]
    )
    route = respx.get(f"{API}/projects").mock(
        side_effect=[
            httpx.Response(401, json={"message": "expired"}),
            httpx.Response(200, json=[{"project_id": "p1"}]),
        ]
    )
    client = make_client()
    out = await client.list("/projects")
    assert out == [{"project_id": "p1"}]
    assert route.call_count == 2
    assert route.calls.last.request.headers["authorization"] == "Bearer NEW"
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_list_limit_applied_clientside():
    respx.post(f"{API}/access/users/login").mock(
        return_value=httpx.Response(200, json={"access_token": "T"})
    )
    respx.get(f"{API}/nodes").mock(
        return_value=httpx.Response(200, json=[{"i": i} for i in range(10)])
    )
    client = make_client()
    out = await client.list("/nodes", limit=3)
    assert out == [{"i": 0}, {"i": 1}, {"i": 2}]
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_error_body_message_surfaced():
    respx.post(f"{API}/access/users/login").mock(
        return_value=httpx.Response(200, json={"access_token": "T"})
    )
    respx.get(f"{API}/projects/x").mock(
        return_value=httpx.Response(404, json={"message": "Project not found"})
    )
    client = make_client()
    with pytest.raises(GNS3Error) as ei:
        await client.get("/projects/x")
    assert "404" in str(ei.value)
    assert "Project not found" in str(ei.value)
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_connect_error_mapped():
    respx.post(f"{API}/access/users/login").mock(
        return_value=httpx.Response(200, json={"access_token": "T"})
    )
    respx.get(f"{API}/version").mock(side_effect=httpx.ConnectError("boom"))
    client = make_client()
    with pytest.raises(GNS3Error) as ei:
        await client.get("/version")
    assert "Cannot reach" in str(ei.value)
    await client.aclose()
