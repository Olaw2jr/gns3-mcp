"""Async HTTP client for the GNS3 v3 controller REST API.

A single :class:`GNS3Client` instance is shared by all tools. It handles bearer-token
login, transparent re-authentication on 401, request execution with sensible errors, and
binary upload/download helpers (project export/import, image upload, capture files).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx

from .config import Settings
from .errors import raise_for_response, wrap_transport_error

JSON = Any


class GNS3Client:
    """Thin async wrapper around the GNS3 v3 API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._token: str | None = settings.token
        self._lock = asyncio.Lock()
        self._client = httpx.AsyncClient(
            base_url=settings.api_base,
            verify=settings.verify_tls,
            timeout=settings.timeout,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------ auth
    async def login(self) -> str:
        """Authenticate and cache a bearer token. Returns the token."""
        s = self._settings
        if s.token:
            self._token = s.token
            return self._token
        if not s.username or not s.password:
            raise wrap_transport_error(
                httpx.HTTPError(  # type: ignore[arg-type]
                    "No credentials: set GNS3_USERNAME/GNS3_PASSWORD or GNS3_TOKEN"
                )
            )
        # /v3/access/users/login expects form-urlencoded username/password.
        resp = await self._client.post(
            "/access/users/login",
            data={"username": s.username, "password": s.password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        raise_for_response(resp)
        self._token = resp.json()["access_token"]
        return self._token

    async def _auth_header(self) -> dict[str, str]:
        if self._token is None:
            async with self._lock:
                if self._token is None:
                    await self.login()
        return {"Authorization": f"Bearer {self._token}"}

    # --------------------------------------------------------------- request
    async def request(
        self,
        method: str,
        path: str,
        *,
        json: JSON | None = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        parse: bool = True,
    ) -> JSON:
        """Execute a request, re-authenticating once on 401.

        Returns parsed JSON (or ``None`` for empty bodies) when ``parse`` is true,
        otherwise the raw :class:`httpx.Response`.
        """
        headers = await self._auth_header()
        try:
            resp = await self._client.request(
                method, path, json=json, params=params, data=data, headers=headers
            )
            if resp.status_code == 401 and not self._settings.token:
                # Token expired/invalid — re-login once and retry.
                async with self._lock:
                    self._token = None
                headers = await self._auth_header()
                resp = await self._client.request(
                    method, path, json=json, params=params, data=data, headers=headers
                )
        except httpx.HTTPError as exc:
            raise wrap_transport_error(exc) from exc

        raise_for_response(resp)
        if not parse:
            return resp
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return resp.text

    # Convenience verbs ----------------------------------------------------
    async def get(self, path: str, **kw: Any) -> JSON:
        return await self.request("GET", path, **kw)

    async def post(self, path: str, **kw: Any) -> JSON:
        return await self.request("POST", path, **kw)

    async def put(self, path: str, **kw: Any) -> JSON:
        return await self.request("PUT", path, **kw)

    async def delete(self, path: str, **kw: Any) -> JSON:
        return await self.request("DELETE", path, **kw)

    async def list(self, path: str, *, limit: int | None = None, **kw: Any) -> list[JSON]:
        """GET a collection endpoint and return a list, applying an optional limit.

        GNS3 v3 returns plain JSON arrays for collections; ``limit`` is applied
        client-side so callers can trim large result sets out of the context window.
        """
        result = await self.get(path, **kw)
        items = result if isinstance(result, list) else (result or [])
        if limit is not None:
            items = items[:limit]
        return items

    # --------------------------------------------------------------- binary
    async def download(self, path: str, dest: str, *, params: dict[str, Any] | None = None) -> str:
        """Stream a binary endpoint (export/capture/image) to a local file path."""
        headers = await self._auth_header()
        dest_path = Path(dest).expanduser()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            async with self._client.stream(
                "GET", path, params=params, headers=headers
            ) as resp:
                raise_for_response(resp)
                with dest_path.open("wb") as fh:
                    async for chunk in resp.aiter_bytes():
                        fh.write(chunk)
        except httpx.HTTPError as exc:
            raise wrap_transport_error(exc) from exc
        return str(dest_path)

    async def send_content(
        self, method: str, path: str, content: bytes, *, parse: bool = True
    ) -> JSON:
        """Send a raw byte body (e.g. write a project/node file). Re-auths on 401."""
        headers = await self._auth_header()
        try:
            resp = await self._client.request(method, path, content=content, headers=headers)
            if resp.status_code == 401 and not self._settings.token:
                async with self._lock:
                    self._token = None
                headers = await self._auth_header()
                resp = await self._client.request(
                    method, path, content=content, headers=headers
                )
        except httpx.HTTPError as exc:
            raise wrap_transport_error(exc) from exc
        raise_for_response(resp)
        if not parse:
            return resp
        return resp.json() if resp.content else None

    async def upload(self, path: str, src: str, *, method: str = "POST") -> JSON:
        """Upload a local file's bytes to a binary endpoint (import/image upload)."""
        headers = await self._auth_header()
        src_path = Path(src).expanduser()
        if not src_path.is_file():
            from .errors import GNS3Error

            raise GNS3Error(f"File not found: {src_path}")
        try:
            resp = await self._client.request(
                method, path, content=src_path.read_bytes(), headers=headers
            )
        except httpx.HTTPError as exc:
            raise wrap_transport_error(exc) from exc
        raise_for_response(resp)
        return resp.json() if resp.content else None

    @property
    def settings(self) -> Settings:
        return self._settings
