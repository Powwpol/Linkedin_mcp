"""Profile search plugin for LinkedIn MCP Server.

Provides tools for searching and retrieving LinkedIn profiles.

LinkedIn API endpoints used:
- GET /v2/userinfo - Get authenticated user's profile (OpenID Connect)
- GET /v2/me - Get authenticated user's basic profile
- GET /rest/people/(id:{id}) - Get profile by person ID
- GET /v2/connections?q=viewer - Browse 1st-degree connections
"""

from __future__ import annotations

from typing import Any

from linkedin_mcp.linkedin_client import LinkedInClient


class ProfilePlugin:
    """Plugin for LinkedIn profile search and retrieval operations."""

    def __init__(self, client: LinkedInClient):
        self.client = client

    async def get_my_profile(self) -> dict[str, Any]:
        """Get the authenticated user's own profile.

        Returns profile information including name, email, picture, and locale.
        Uses the OpenID Connect /v2/userinfo endpoint.
        """
        return await self.client.get("/v2/userinfo")

    async def get_my_profile_details(self) -> dict[str, Any]:
        """Get the authenticated user's detailed profile via /v2/me.

        Returns localizedFirstName, localizedLastName, id, profilePicture, etc.
        """
        return await self.client.get("/v2/me")

    async def get_profile_by_id(self, person_id: str) -> dict[str, Any]:
        """Get a LinkedIn profile by person ID.

        Args:
            person_id: The LinkedIn person ID (e.g., from a URN urn:li:person:{id}).

        Returns:
            Profile data for the specified person.
        """
        path = f"/rest/people/(id:{person_id})"
        return await self.client.get(path)

    async def get_connections(
        self, start: int = 0, count: int = 50
    ) -> dict[str, Any]:
        """Get the authenticated user's 1st-degree connections.

        Args:
            start: Pagination offset (default 0).
            count: Number of connections to return (max 50).

        Returns:
            Paginated list of connection URNs.
        """
        count = min(count, 50)  # LinkedIn max is 50
        return await self.client.get(
            "/v2/connections",
            params={"q": "viewer", "start": start, "count": count},
        )

    async def search_people_by_keyword(
        self,
        keywords: str,
        start: int = 0,
        count: int = 10,
    ) -> dict[str, Any]:
        """Search for people using keywords.

        Uses the Community Management API people search endpoint.

        Args:
            keywords: Search query (name, title, company, etc.).
            start: Pagination offset.
            count: Number of results to return (max 50).

        Returns:
            Search results with profile summaries.

        Note:
            This endpoint requires the 'r_member_social' scope and
            Community Management API access.
        """
        count = min(count, 50)
        return await self.client.get(
            "/rest/people",
            params={
                "q": "keyword",
                "keyword": keywords,
                "start": start,
                "count": count,
            },
        )

    async def search_people_by_connections(
        self,
        keywords: str | None = None,
        start: int = 0,
        count: int = 10,
    ) -> dict[str, Any]:
        """Search within 1st-degree connections with optional keyword filter.

        Browses the user's network connections and allows filtering.

        Args:
            keywords: Optional keyword filter for connection names/titles.
            start: Pagination offset.
            count: Number of results.

        Returns:
            List of matching connections.
        """
        count = min(count, 50)
        params: dict[str, Any] = {
            "q": "viewer",
            "start": start,
            "count": count,
        }
        if keywords:
            params["keywords"] = keywords
        return await self.client.get("/v2/connections", params=params)

    async def get_profile_network_info(self) -> dict[str, Any]:
        """Get the authenticated user's network size information.

        Returns:
            Network statistics including connection count.
        """
        user_info = await self.client.get_current_user()
        person_id = user_info["sub"]
        urn = f"urn:li:person:{person_id}"
        encoded_urn = self.client.encode_urn(urn)
        return await self.client.get(f"/v2/networkSizes/{encoded_urn}?edgeType=CompanyFollowedByMember")
