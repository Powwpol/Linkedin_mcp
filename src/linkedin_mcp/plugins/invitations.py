"""Invitation plugin for LinkedIn MCP Server.

Provides tools for sending, managing, and responding to LinkedIn connection invitations.

LinkedIn API endpoints used:
- POST /v2/invitations - Send a connection invitation
- GET /v2/invitations - List received invitations
- POST /v2/invitations/{key}?action=accept - Accept invitation
- POST /v2/invitations/{key}?action=ignore - Ignore invitation
"""

from __future__ import annotations

from typing import Any

from linkedin_mcp.linkedin_client import LinkedInClient


class InvitationPlugin:
    """Plugin for LinkedIn invitation/connection request operations."""

    def __init__(self, client: LinkedInClient):
        self.client = client

    async def send_invitation(
        self,
        person_id: str,
        message: str | None = None,
    ) -> dict[str, Any]:
        """Send a connection invitation to a LinkedIn member.

        Args:
            person_id: The target person's LinkedIn ID (the {id} part
                       from urn:li:person:{id}).
            message: Optional personalized message to include with the
                     invitation (max 300 characters).

        Returns:
            API response confirming the invitation was sent.

        Note:
            - LinkedIn limits invitation messages to 300 characters
            - Sending too many invitations can trigger rate limits or account restrictions
        """
        invitee_urn = f"urn:li:person:{person_id}"

        body: dict[str, Any] = {
            "invitee": invitee_urn,
            "message": {
                "text": message[:300] if message else "",
            },
        }

        # If no message, remove the message field entirely
        if not message:
            body.pop("message", None)

        return await self.client.post("/v2/invitations", json_body=body)

    async def send_invitation_by_email(
        self,
        email: str,
        first_name: str,
        last_name: str,
        message: str | None = None,
    ) -> dict[str, Any]:
        """Send a connection invitation using an email address.

        This is used when you don't have the person's LinkedIn ID but
        have their email address.

        Args:
            email: The target person's email address.
            first_name: The target person's first name.
            last_name: The target person's last name.
            message: Optional personalized message (max 300 characters).

        Returns:
            API response confirming the invitation was sent.
        """
        body: dict[str, Any] = {
            "invitee": {
                "com.linkedin.voyager.growth.invitation.InviteeProfile": {
                    "profileId": email,
                }
            },
            "message": {
                "text": message[:300] if message else "",
            },
        }

        if not message:
            body.pop("message", None)

        return await self.client.post("/v2/invitations", json_body=body)

    async def get_received_invitations(
        self,
        start: int = 0,
        count: int = 20,
    ) -> dict[str, Any]:
        """Get pending received connection invitations.

        Args:
            start: Pagination offset.
            count: Number of invitations to retrieve (max 50).

        Returns:
            Paginated list of received invitations.
        """
        count = min(count, 50)
        return await self.client.get(
            "/v2/invitations",
            params={
                "q": "received",
                "start": start,
                "count": count,
            },
        )

    async def get_sent_invitations(
        self,
        start: int = 0,
        count: int = 20,
    ) -> dict[str, Any]:
        """Get sent connection invitations.

        Args:
            start: Pagination offset.
            count: Number of invitations to retrieve (max 50).

        Returns:
            Paginated list of sent invitations with their status.
        """
        count = min(count, 50)
        return await self.client.get(
            "/v2/invitations",
            params={
                "q": "sent",
                "start": start,
                "count": count,
            },
        )

    async def accept_invitation(self, invitation_urn: str) -> dict[str, Any]:
        """Accept a received connection invitation.

        Args:
            invitation_urn: The invitation URN to accept
                            (e.g., urn:li:invitation:{id}).

        Returns:
            API response confirming acceptance.
        """
        encoded = self.client.encode_urn(invitation_urn)
        return await self.client.post(
            f"/v2/invitations/{encoded}?action=accept",
            json_body={},
        )

    async def ignore_invitation(self, invitation_urn: str) -> dict[str, Any]:
        """Ignore (reject) a received connection invitation.

        Args:
            invitation_urn: The invitation URN to ignore.

        Returns:
            API response confirming the invitation was ignored.
        """
        encoded = self.client.encode_urn(invitation_urn)
        return await self.client.post(
            f"/v2/invitations/{encoded}?action=ignore",
            json_body={},
        )

    async def withdraw_invitation(self, invitation_urn: str) -> dict[str, Any]:
        """Withdraw a sent invitation that hasn't been accepted yet.

        Args:
            invitation_urn: The invitation URN to withdraw.

        Returns:
            API response confirming withdrawal.
        """
        encoded = self.client.encode_urn(invitation_urn)
        return await self.client.post(
            f"/v2/invitations/{encoded}?action=withdraw",
            json_body={},
        )
