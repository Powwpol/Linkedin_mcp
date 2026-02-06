"""LinkedIn OAuth 2.0 authentication module.

Implements the 3-legged OAuth2 authorization code flow as documented at:
https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow
"""

from __future__ import annotations

import secrets
from urllib.parse import urlencode

import httpx

from linkedin_mcp.config import Settings, TokenStore


class LinkedInAuth:
    """Handles LinkedIn OAuth 2.0 3-legged authentication flow."""

    def __init__(self, settings: Settings, token_store: TokenStore):
        self.settings = settings
        self.token_store = token_store
        self._state: str | None = None

    def get_authorization_url(self) -> str:
        """Generate the LinkedIn authorization URL (Step 1).

        Returns the URL to redirect the user to for granting authorization.
        """
        self._state = secrets.token_urlsafe(32)
        params = {
            "response_type": "code",
            "client_id": self.settings.linkedin_client_id,
            "redirect_uri": self.settings.linkedin_redirect_uri,
            "state": self._state,
            "scope": self.settings.linkedin_scopes,
        }
        return f"{self.settings.authorization_url}?{urlencode(params)}"

    @property
    def expected_state(self) -> str | None:
        return self._state

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token (Step 2).

        Args:
            code: The authorization code received from LinkedIn callback.

        Returns:
            Token response dict with access_token, expires_in, etc.

        Raises:
            httpx.HTTPStatusError: If the token exchange request fails.
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.settings.linkedin_client_id,
            "client_secret": self.settings.linkedin_client_secret,
            "redirect_uri": self.settings.linkedin_redirect_uri,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.settings.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token_data = response.json()

        self.token_store.store_tokens(
            access_token=token_data["access_token"],
            expires_in=token_data.get("expires_in", 5184000),
            refresh_token=token_data.get("refresh_token"),
            refresh_token_expires_in=token_data.get("refresh_token_expires_in"),
            scope=token_data.get("scope"),
        )
        return token_data

    async def refresh_access_token(self) -> dict:
        """Refresh the access token using the refresh token.

        Returns:
            New token response dict.

        Raises:
            ValueError: If no refresh token is available.
            httpx.HTTPStatusError: If the refresh request fails.
        """
        if not self.token_store.refresh_token:
            raise ValueError("No refresh token available. Re-authenticate via OAuth flow.")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.token_store.refresh_token,
            "client_id": self.settings.linkedin_client_id,
            "client_secret": self.settings.linkedin_client_secret,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.settings.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token_data = response.json()

        self.token_store.store_tokens(
            access_token=token_data["access_token"],
            expires_in=token_data.get("expires_in", 5184000),
            refresh_token=token_data.get("refresh_token", self.token_store.refresh_token),
            refresh_token_expires_in=token_data.get("refresh_token_expires_in"),
            scope=token_data.get("scope"),
        )
        return token_data

    def is_authenticated(self) -> bool:
        """Check if we have a stored access token."""
        return self.token_store.is_authenticated()

    def get_access_token(self) -> str:
        """Get the current access token.

        Raises:
            ValueError: If not authenticated.
        """
        token = self.token_store.access_token
        if not token:
            raise ValueError(
                "Not authenticated. Visit /auth/login to start the OAuth flow."
            )
        return token

    def logout(self) -> None:
        """Clear stored tokens."""
        self.token_store.clear()
