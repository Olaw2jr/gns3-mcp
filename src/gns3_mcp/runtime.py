"""Process-wide runtime state shared by tool modules.

The server initialises a single :class:`GNS3Client` and :class:`Settings` at startup and
stores them here so tool functions can reach them without per-call wiring.
"""

from __future__ import annotations

from .client import GNS3Client
from .config import Settings, get_settings

_settings: Settings | None = None
_client: GNS3Client | None = None


def init_runtime(settings: Settings | None = None) -> Settings:
    """Initialise settings and the GNS3 client. Returns the active settings."""
    global _settings, _client
    _settings = settings or get_settings()
    _client = GNS3Client(_settings)
    return _settings


def get_client() -> GNS3Client:
    if _client is None:
        init_runtime()
    assert _client is not None
    return _client


def get_runtime_settings() -> Settings:
    if _settings is None:
        init_runtime()
    assert _settings is not None
    return _settings


def read_only() -> bool:
    return get_runtime_settings().read_only


async def shutdown() -> None:
    if _client is not None:
        await _client.aclose()
