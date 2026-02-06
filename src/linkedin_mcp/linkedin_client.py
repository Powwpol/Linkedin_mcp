"""LinkedIn API HTTP client.

Centralized client for making authenticated requests to the LinkedIn REST API.
Handles headers, URN encoding, error handling, and rate limiting.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from linkedin_mcp.config import Settings


class LinkedInAPIError(Exception):
    """Raised when a LinkedIn API request fails."""

    def __init__(self, status_code: int, message: str, details: Any = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"LinkedIn API Error {status_code}: {message}")


class LinkedInClient:
    """Async HTTP client for the LinkedIn REST API."""

    def __init__(self, settings: Settings, access_token: str):
        self.settings = settings
        self.access_token = access_token
        self.base_url = settings.api_base_url
        self.api_version = settings.linkedin_api_version

    @property
    def _default_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": self.api_version,
            "Content-Type": "application/json",
        }

    @staticmethod
    def encode_urn(urn: str) -> str:
        """URL-encode a LinkedIn URN for use in URL paths/params."""
        return quote(urn, safe="")

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make an authenticated request to the LinkedIn API.

        Raises:
            LinkedInAPIError: On non-2xx responses.
        """
        url = f"{self.base_url}{path}"
        headers = {**self._default_headers, **(extra_headers or {})}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
                headers=headers,
            )

        if response.status_code >= 400:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            raise LinkedInAPIError(
                status_code=response.status_code,
                message=f"{method} {path} failed",
                details=error_detail,
            )

        return response

    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a GET request and return JSON response."""
        resp = await self._request("GET", path, params=params)
        if resp.status_code == 204:
            return {}
        return resp.json()

    async def post(
        self,
        path: str,
        json_body: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | str:
        """Make a POST request. Returns JSON body or x-restli-id header."""
        resp = await self._request(
            "POST", path, json_body=json_body, extra_headers=extra_headers
        )
        # For 201 Created responses, the ID is often in the header
        restli_id = resp.headers.get("x-restli-id")
        if resp.status_code == 201:
            try:
                body = resp.json()
                if restli_id:
                    body["_restli_id"] = restli_id
                return body
            except Exception:
                return {"_restli_id": restli_id} if restli_id else {}
        if resp.status_code == 204:
            return {"_restli_id": restli_id} if restli_id else {}
        try:
            return resp.json()
        except Exception:
            return {}

    async def delete(self, path: str) -> bool:
        """Make a DELETE request. Returns True on success."""
        await self._request("DELETE", path)
        return True

    # --- Convenience: Get current user's profile info ---

    async def get_current_user(self) -> dict[str, Any]:
        """Get the authenticated user's profile via /v2/userinfo (OpenID)."""
        return await self.get("/v2/userinfo")

    async def get_current_user_id(self) -> str:
        """Get the authenticated user's person URN sub value."""
        info = await self.get_current_user()
        return info["sub"]
