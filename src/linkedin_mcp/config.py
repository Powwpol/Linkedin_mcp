"""Configuration module for LinkedIn MCP Server."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    linkedin_client_id: str = Field(default="", description="LinkedIn OAuth2 Client ID")
    linkedin_client_secret: str = Field(default="", description="LinkedIn OAuth2 Client Secret")
    linkedin_redirect_uri: str = Field(
        default="http://localhost:8000/auth/callback",
        description="OAuth2 callback URL",
    )
    linkedin_scopes: str = Field(
        default="openid profile email w_member_social",
        description="Space-separated OAuth2 scopes",
    )
    linkedin_api_version: str = Field(
        default="202601",
        description="LinkedIn API version (YYYYMM)",
    )
    fastapi_host: str = Field(default="0.0.0.0", description="FastAPI host")
    fastapi_port: int = Field(default=8000, description="FastAPI port")
    token_store_path: str = Field(
        default="token_store.json",
        description="Path to store OAuth tokens",
    )

    # --- ChatGPT POC settings ---
    base_url: str = Field(
        default="http://localhost:8000",
        description="Public base URL (e.g. https://xxx.ngrok-free.app)",
    )
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for signing session cookies",
    )
    db_path: str = Field(
        default="linkedin_sessions.db",
        description="SQLite database path for multi-user token storage",
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def scopes_list(self) -> list[str]:
        return self.linkedin_scopes.split()

    @property
    def authorization_url(self) -> str:
        return "https://www.linkedin.com/oauth/v2/authorization"

    @property
    def token_url(self) -> str:
        return "https://www.linkedin.com/oauth/v2/accessToken"

    @property
    def api_base_url(self) -> str:
        return "https://api.linkedin.com"


class TokenStore:
    """Persistent token storage using a JSON file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2))

    @property
    def access_token(self) -> str | None:
        return self._data.get("access_token")

    @property
    def refresh_token(self) -> str | None:
        return self._data.get("refresh_token")

    def store_tokens(
        self,
        access_token: str,
        expires_in: int,
        refresh_token: str | None = None,
        refresh_token_expires_in: int | None = None,
        scope: str | None = None,
    ) -> None:
        self._data = {
            "access_token": access_token,
            "expires_in": expires_in,
            "refresh_token": refresh_token,
            "refresh_token_expires_in": refresh_token_expires_in,
            "scope": scope,
        }
        self._save()

    def clear(self) -> None:
        self._data = {}
        if self.path.exists():
            self.path.unlink()

    def is_authenticated(self) -> bool:
        return self.access_token is not None


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


def get_token_store(settings: Settings | None = None) -> TokenStore:
    """Get token store instance."""
    if settings is None:
        settings = get_settings()
    return TokenStore(settings.token_store_path)
