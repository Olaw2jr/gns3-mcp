"""Error helpers that turn GNS3/httpx failures into concise MCP tool errors."""

from __future__ import annotations

import httpx
from fastmcp.exceptions import ToolError


class GNS3Error(ToolError):
    """A GNS3 controller error surfaced to the MCP client."""


def raise_for_response(response: httpx.Response) -> None:
    """Raise a clean :class:`GNS3Error` for a non-2xx GNS3 response.

    GNS3 returns ``{"status": <code>, "message": "..."}`` bodies for most errors; we
    extract that message and add a hint for the common "project not open" case.
    """
    if response.is_success:
        return

    message = response.reason_phrase
    try:
        body = response.json()
        if isinstance(body, dict):
            message = body.get("message") or body.get("detail") or message
    except (ValueError, TypeError):
        text = response.text.strip()
        if text:
            message = text[:500]

    code = response.status_code
    hint = ""
    if code == 401:
        hint = " (check GNS3_USERNAME/GNS3_PASSWORD or GNS3_TOKEN)"
    elif code == 403:
        hint = " (the authenticated user lacks the required privilege)"
    elif code == 409 and "open" in message.lower():
        hint = " — open the project first with project_open"

    raise GNS3Error(f"GNS3 {code}: {message}{hint}")


def wrap_transport_error(exc: httpx.HTTPError) -> GNS3Error:
    """Convert a transport-level httpx error into a GNS3Error."""
    if isinstance(exc, httpx.ConnectError):
        return GNS3Error(
            "Cannot reach the GNS3 controller — is it running and is GNS3_BASE_URL correct?"
        )
    if isinstance(exc, httpx.TimeoutException):
        return GNS3Error("GNS3 controller request timed out.")
    return GNS3Error(f"GNS3 transport error: {exc}")
