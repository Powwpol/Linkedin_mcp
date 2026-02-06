"""Post publishing plugin for LinkedIn MCP Server.

Provides tools for creating, reading, updating, and deleting LinkedIn posts.

LinkedIn API endpoints used:
- POST /rest/posts - Create a new post
- GET /rest/posts/{urn} - Get a post by URN
- GET /rest/posts?q=author&author={urn} - Get posts by author
- POST /rest/posts/{urn} (PARTIAL_UPDATE) - Update a post
- DELETE /rest/posts/{urn} - Delete a post
- POST /rest/images?action=initializeUpload - Initialize image upload
- PUT {uploadUrl} - Upload image binary
"""

from __future__ import annotations

from typing import Any

import httpx

from linkedin_mcp.linkedin_client import LinkedInClient


class PostPlugin:
    """Plugin for LinkedIn post publishing operations."""

    def __init__(self, client: LinkedInClient):
        self.client = client

    async def create_text_post(
        self,
        text: str,
        visibility: str = "PUBLIC",
        author_urn: str | None = None,
    ) -> dict[str, Any]:
        """Create a text-only post on LinkedIn.

        Args:
            text: The post content/commentary. Supports hashtags (#topic)
                  and mentions (@[Name](urn:li:person:{id})).
            visibility: Post visibility - PUBLIC, CONNECTIONS, or LOGGED_IN.
            author_urn: Author URN (e.g., urn:li:person:{id}). If None,
                        uses the authenticated user.

        Returns:
            Dict with post URN in '_restli_id' key.
        """
        if not author_urn:
            user_id = await self.client.get_current_user_id()
            author_urn = f"urn:li:person:{user_id}"

        body = {
            "author": author_urn,
            "commentary": text,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return await self.client.post("/rest/posts", json_body=body)

    async def create_post_with_link(
        self,
        text: str,
        link_url: str,
        link_title: str | None = None,
        link_description: str | None = None,
        visibility: str = "PUBLIC",
        author_urn: str | None = None,
    ) -> dict[str, Any]:
        """Create a post with an article/link attachment.

        Args:
            text: Post commentary text.
            link_url: URL of the article to attach.
            link_title: Optional title for the article preview.
            link_description: Optional description for the article preview.
            visibility: Post visibility.
            author_urn: Author URN. If None, uses authenticated user.

        Returns:
            Dict with post URN.
        """
        if not author_urn:
            user_id = await self.client.get_current_user_id()
            author_urn = f"urn:li:person:{user_id}"

        article: dict[str, Any] = {"source": link_url}
        if link_title:
            article["title"] = link_title
        if link_description:
            article["description"] = link_description

        body = {
            "author": author_urn,
            "commentary": text,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {"article": article},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return await self.client.post("/rest/posts", json_body=body)

    async def create_post_with_image(
        self,
        text: str,
        image_path: str,
        alt_text: str = "",
        visibility: str = "PUBLIC",
        author_urn: str | None = None,
    ) -> dict[str, Any]:
        """Create a post with an image attachment.

        This performs a 3-step process:
        1. Initialize the image upload to get an upload URL and image URN
        2. Upload the image binary to the upload URL
        3. Create the post referencing the image URN

        Args:
            text: Post commentary text.
            image_path: Local file path to the image (JPG, PNG, or GIF).
            alt_text: Accessibility alt text for the image.
            visibility: Post visibility.
            author_urn: Author URN. If None, uses authenticated user.

        Returns:
            Dict with post URN.
        """
        if not author_urn:
            user_id = await self.client.get_current_user_id()
            author_urn = f"urn:li:person:{user_id}"

        # Step 1: Initialize upload
        init_body = {"initializeUploadRequest": {"owner": author_urn}}
        init_resp = await self.client.post(
            "/rest/images?action=initializeUpload", json_body=init_body
        )
        upload_url = init_resp["value"]["uploadUrl"]
        image_urn = init_resp["value"]["image"]

        # Step 2: Upload image binary
        with open(image_path, "rb") as f:
            image_data = f.read()

        async with httpx.AsyncClient(timeout=60.0) as http_client:
            upload_resp = await http_client.put(
                upload_url,
                content=image_data,
                headers={
                    "Authorization": f"Bearer {self.client.access_token}",
                    "Content-Type": "application/octet-stream",
                },
            )
            upload_resp.raise_for_status()

        # Step 3: Create post with image
        body = {
            "author": author_urn,
            "commentary": text,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "media": {
                    "altText": alt_text,
                    "id": image_urn,
                },
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return await self.client.post("/rest/posts", json_body=body)

    async def get_post(self, post_urn: str) -> dict[str, Any]:
        """Get a specific post by its URN.

        Args:
            post_urn: The post URN (e.g., urn:li:share:{id} or urn:li:ugcPost:{id}).

        Returns:
            Post data including author, commentary, visibility, etc.
        """
        encoded = self.client.encode_urn(post_urn)
        return await self.client.get(f"/rest/posts/{encoded}?viewContext=AUTHOR")

    async def get_my_posts(
        self, count: int = 10, author_urn: str | None = None
    ) -> dict[str, Any]:
        """Get posts authored by the authenticated user (or specified author).

        Args:
            count: Number of posts to retrieve (default 10).
            author_urn: Author URN. If None, uses authenticated user.

        Returns:
            Paginated list of posts.
        """
        if not author_urn:
            user_id = await self.client.get_current_user_id()
            author_urn = f"urn:li:person:{user_id}"

        encoded_author = self.client.encode_urn(author_urn)
        return await self.client.get(
            "/rest/posts",
            params={
                "q": "author",
                "author": encoded_author,
                "count": count,
                "sortBy": "LAST_MODIFIED",
            },
        )

    async def delete_post(self, post_urn: str) -> bool:
        """Delete a post by its URN.

        Args:
            post_urn: The post URN to delete.

        Returns:
            True if successfully deleted.
        """
        encoded = self.client.encode_urn(post_urn)
        return await self.client.delete(f"/rest/posts/{encoded}")

    async def create_reshare(
        self,
        original_post_urn: str,
        text: str = "",
        visibility: str = "PUBLIC",
        author_urn: str | None = None,
    ) -> dict[str, Any]:
        """Reshare an existing post with optional commentary.

        Args:
            original_post_urn: URN of the post to reshare.
            text: Optional commentary to add to the reshare.
            visibility: Post visibility.
            author_urn: Author URN. If None, uses authenticated user.

        Returns:
            Dict with reshare post URN.
        """
        if not author_urn:
            user_id = await self.client.get_current_user_id()
            author_urn = f"urn:li:person:{user_id}"

        body = {
            "author": author_urn,
            "commentary": text,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "reshareContext": {"parent": original_post_urn},
        }
        return await self.client.post("/rest/posts", json_body=body)
