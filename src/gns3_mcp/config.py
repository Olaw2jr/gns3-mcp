"""Configuration for the GNS3 v3 MCP server, sourced from environment variables.

All settings are read from the process environment (prefix ``GNS3_``) so they can be
supplied through the MCP client's server declaration (``.mcp.json`` / Claude Desktop JSON)
or the shell.
"""

from __future__ import annotations

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the server and the GNS3 controller client."""

    model_config = SettingsConfigDict(env_prefix="GNS3_", extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _drop_empty(cls, values: Any) -> Any:
        """Treat empty-string env values (e.g. unexpanded ``${VAR}``) as unset.

        This keeps plugin ``.mcp.json`` env blocks robust: a client that passes an empty
        string for an unset variable falls back to the field default instead of overriding
        it with "".
        """
        if isinstance(values, dict):
            return {k: v for k, v in values.items() if v != ""}
        return values

    # --- Controller connection ---
    base_url: str = Field(
        default="http://localhost:3080",
        description="GNS3 v3 controller base URL (no trailing /v3).",
    )
    username: str | None = Field(default=None, description="Controller username for login.")
    password: str | None = Field(default=None, description="Controller password for login.")
    token: str | None = Field(
        default=None,
        description="Pre-issued bearer token; if set, username/password login is skipped.",
    )
    verify_tls: bool = Field(default=True, description="Verify TLS certificates for https URLs.")
    timeout: float = Field(default=30.0, description="Per-request timeout in seconds.")

    # --- Behaviour ---
    default_project: str | None = Field(
        default=None,
        description="Optional project id used when a tool omits project_id.",
    )
    read_only: bool = Field(
        default=False,
        description="When true, mutating/destructive tools are not registered.",
    )

    # --- Console automation ---
    console_timeout: float = Field(
        default=15.0, description="Default read timeout (s) for node console interactions."
    )

    # --- Transport ---
    transport: str = Field(
        default="stdio", description="MCP transport: 'stdio' or 'http'."
    )
    http_host: str = Field(default="127.0.0.1", description="Bind host for http transport.")
    http_port: int = Field(default=8080, description="Bind port for http transport.")

    @property
    def api_base(self) -> str:
        """Base URL including the ``/v3`` API prefix."""
        return self.base_url.rstrip("/") + "/v3"


def get_settings() -> Settings:
    """Build a :class:`Settings` instance from the environment."""
    return Settings()
