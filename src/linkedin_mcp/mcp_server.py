"""LinkedIn MCP Server - Model Context Protocol server for LinkedIn API.

Exposes LinkedIn API operations as MCP tools that can be used by AI agents:
- Profile search and retrieval
- Post creation and management
- Connection invitation management

Uses the FastMCP framework for tool registration and server lifecycle.

Run with: python -m linkedin_mcp.mcp_server
Or via entry point: linkedin-mcp
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from linkedin_mcp.auth import LinkedInAuth
from linkedin_mcp.config import Settings, get_settings, get_token_store
from linkedin_mcp.linkedin_client import LinkedInAPIError, LinkedInClient
from linkedin_mcp.plugins.invitations import InvitationPlugin
from linkedin_mcp.plugins.posts import PostPlugin
from linkedin_mcp.plugins.profiles import ProfilePlugin

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "LinkedIn MCP Server",
    instructions=(
        "MCP server providing LinkedIn API tools: "
        "profile search, post publishing, and invitation management. "
        "Requires OAuth2 authentication via the companion FastAPI server."
    ),
)

settings: Settings = get_settings()
token_store = get_token_store(settings)
auth_manager = LinkedInAuth(settings, token_store)


def _get_client() -> LinkedInClient:
    """Get an authenticated LinkedIn client. Raises if not authenticated."""
    token = auth_manager.get_access_token()
    return LinkedInClient(settings, token)


def _format_result(data: Any) -> str:
    """Format API response data as readable JSON string."""
    if isinstance(data, dict):
        return json.dumps(data, indent=2, ensure_ascii=False)
    return str(data)


def _error_response(error: Exception) -> str:
    """Format an error as a user-friendly message."""
    if isinstance(error, LinkedInAPIError):
        return json.dumps(
            {
                "error": True,
                "status_code": error.status_code,
                "message": error.message,
                "details": error.details,
            },
            indent=2,
            ensure_ascii=False,
        )
    if isinstance(error, ValueError):
        return json.dumps(
            {"error": True, "message": str(error)},
            indent=2,
            ensure_ascii=False,
        )
    return json.dumps(
        {"error": True, "message": f"Unexpected error: {error}"},
        indent=2,
        ensure_ascii=False,
    )


# ===========================================================================
#  AUTH TOOLS
# ===========================================================================


@mcp.tool()
def linkedin_auth_status() -> str:
    """Check if the LinkedIn OAuth2 authentication is active.

    Returns the current authentication status. If not authenticated,
    you need to visit the FastAPI server's /auth/login endpoint first.
    """
    authenticated = auth_manager.is_authenticated()
    if authenticated:
        return json.dumps({
            "authenticated": True,
            "message": "LinkedIn OAuth2 token is active. You can use all LinkedIn tools.",
        })
    return json.dumps({
        "authenticated": False,
        "message": (
            "Not authenticated. Start the FastAPI server (linkedin-api) "
            "and visit http://localhost:8000/auth/login to authenticate."
        ),
    })


@mcp.tool()
def linkedin_get_auth_url() -> str:
    """Get the LinkedIn OAuth2 authorization URL.

    Returns the URL that the user must visit in their browser to
    grant access to their LinkedIn account.
    """
    if not settings.linkedin_client_id:
        return json.dumps({
            "error": True,
            "message": "LINKEDIN_CLIENT_ID not configured. Set it in the .env file.",
        })
    url = auth_manager.get_authorization_url()
    return json.dumps({
        "authorization_url": url,
        "instructions": "Open this URL in a browser to authenticate with LinkedIn.",
    })


# ===========================================================================
#  PROFILE TOOLS
# ===========================================================================


@mcp.tool()
async def linkedin_get_my_profile() -> str:
    """Get the authenticated LinkedIn user's profile.

    Returns the user's name, email, profile picture, and locale information
    from the OpenID Connect userinfo endpoint.

    Requires: Active OAuth2 authentication with 'openid profile email' scopes.
    """
    try:
        client = _get_client()
        plugin = ProfilePlugin(client)
        result = await plugin.get_my_profile()
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_get_my_profile_details() -> str:
    """Get detailed profile information of the authenticated user.

    Returns localizedFirstName, localizedLastName, profile ID, and
    profilePicture data from the /v2/me endpoint.

    Requires: Active OAuth2 authentication with 'profile' scope.
    """
    try:
        client = _get_client()
        plugin = ProfilePlugin(client)
        result = await plugin.get_my_profile_details()
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_get_profile(person_id: str) -> str:
    """Get a LinkedIn profile by person ID.

    Args:
        person_id: The LinkedIn person ID (the {id} from urn:li:person:{id}).

    Returns profile data for the specified person.
    """
    try:
        client = _get_client()
        plugin = ProfilePlugin(client)
        result = await plugin.get_profile_by_id(person_id)
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_get_connections(start: int = 0, count: int = 50) -> str:
    """Get the authenticated user's 1st-degree LinkedIn connections.

    Args:
        start: Pagination offset (default 0).
        count: Number of connections to return (max 50).

    Returns a paginated list of connection URNs.
    """
    try:
        client = _get_client()
        plugin = ProfilePlugin(client)
        result = await plugin.get_connections(start=start, count=count)
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_search_people(
    keywords: str, start: int = 0, count: int = 10
) -> str:
    """Search for LinkedIn people/profiles by keywords.

    Args:
        keywords: Search query - can be a name, job title, company, skill, etc.
        start: Pagination offset (default 0).
        count: Number of results to return (max 50, default 10).

    Returns matching profiles with basic information.
    Requires Community Management API access with 'r_member_social' scope.
    """
    try:
        client = _get_client()
        plugin = ProfilePlugin(client)
        result = await plugin.search_people_by_keyword(
            keywords=keywords, start=start, count=count
        )
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_search_connections(
    keywords: str = "", start: int = 0, count: int = 10
) -> str:
    """Search within the user's 1st-degree connections.

    Args:
        keywords: Optional filter for connection names/titles.
        start: Pagination offset (default 0).
        count: Number of results (max 50, default 10).

    Returns matching connections from the user's network.
    """
    try:
        client = _get_client()
        plugin = ProfilePlugin(client)
        result = await plugin.search_people_by_connections(
            keywords=keywords or None, start=start, count=count
        )
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


# ===========================================================================
#  POST TOOLS
# ===========================================================================


@mcp.tool()
async def linkedin_create_text_post(
    text: str, visibility: str = "PUBLIC"
) -> str:
    """Create a text-only post on LinkedIn.

    Args:
        text: The post content. Supports:
              - Hashtags: #topic
              - Mentions: @[Person Name](urn:li:person:{id})
              - Line breaks for formatting
        visibility: Who can see the post:
                    - PUBLIC: Anyone on LinkedIn
                    - CONNECTIONS: Only 1st-degree connections
                    - LOGGED_IN: Any logged-in LinkedIn member

    Returns the post URN on success.
    Requires: 'w_member_social' scope.
    """
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        result = await plugin.create_text_post(text=text, visibility=visibility)
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_create_link_post(
    text: str,
    link_url: str,
    link_title: str = "",
    link_description: str = "",
    visibility: str = "PUBLIC",
) -> str:
    """Create a LinkedIn post with a link/article attachment.

    The link will be rendered as a rich preview card with title,
    description, and thumbnail (auto-fetched from the URL).

    Args:
        text: Post commentary text.
        link_url: URL of the article or webpage to attach.
        link_title: Optional title for the link preview card.
        link_description: Optional description for the link preview.
        visibility: Post visibility (PUBLIC, CONNECTIONS, LOGGED_IN).

    Returns the post URN on success.
    """
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        result = await plugin.create_post_with_link(
            text=text,
            link_url=link_url,
            link_title=link_title or None,
            link_description=link_description or None,
            visibility=visibility,
        )
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_create_image_post(
    text: str,
    image_path: str,
    alt_text: str = "",
    visibility: str = "PUBLIC",
) -> str:
    """Create a LinkedIn post with an image attachment.

    Uploads the image to LinkedIn and creates a post referencing it.
    Supported formats: JPG, PNG, GIF (up to 250 frames).

    Args:
        text: Post commentary text.
        image_path: Local file path to the image to upload.
        alt_text: Accessibility alt text describing the image.
        visibility: Post visibility (PUBLIC, CONNECTIONS, LOGGED_IN).

    Returns the post URN on success.
    """
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        result = await plugin.create_post_with_image(
            text=text,
            image_path=image_path,
            alt_text=alt_text,
            visibility=visibility,
        )
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_get_my_posts(count: int = 10) -> str:
    """Get the authenticated user's recent LinkedIn posts.

    Args:
        count: Number of posts to retrieve (default 10).

    Returns a list of posts sorted by last modification date.
    """
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        result = await plugin.get_my_posts(count=count)
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_get_post(post_urn: str) -> str:
    """Get a specific LinkedIn post by its URN.

    Args:
        post_urn: The full post URN (e.g., urn:li:share:123456 or
                  urn:li:ugcPost:123456).

    Returns the post data including author, text, visibility, and engagement.
    """
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        result = await plugin.get_post(post_urn)
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_delete_post(post_urn: str) -> str:
    """Delete a LinkedIn post.

    Args:
        post_urn: The URN of the post to delete.

    Returns confirmation of deletion. This action cannot be undone.
    """
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        await plugin.delete_post(post_urn)
        return json.dumps({"success": True, "message": f"Post {post_urn} deleted."})
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_reshare_post(
    original_post_urn: str, text: str = "", visibility: str = "PUBLIC"
) -> str:
    """Reshare an existing LinkedIn post with optional commentary.

    Args:
        original_post_urn: URN of the original post to reshare.
        text: Optional commentary to add to the reshare.
        visibility: Post visibility (PUBLIC, CONNECTIONS, LOGGED_IN).

    Returns the reshare post URN on success.
    """
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        result = await plugin.create_reshare(
            original_post_urn=original_post_urn,
            text=text,
            visibility=visibility,
        )
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


# ===========================================================================
#  INVITATION TOOLS
# ===========================================================================


@mcp.tool()
async def linkedin_send_invitation(
    person_id: str, message: str = ""
) -> str:
    """Send a LinkedIn connection invitation to a person.

    Args:
        person_id: The target person's LinkedIn ID
                   (the {id} part from urn:li:person:{id}).
        message: Optional personalized message (max 300 characters).
                 Personalized messages increase acceptance rates.

    Returns confirmation that the invitation was sent.
    Note: LinkedIn may restrict accounts that send too many invitations.
    """
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        result = await plugin.send_invitation(
            person_id=person_id,
            message=message or None,
        )
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_send_invitation_by_email(
    email: str, first_name: str, last_name: str, message: str = ""
) -> str:
    """Send a LinkedIn connection invitation using an email address.

    Use this when you have someone's email but not their LinkedIn ID.

    Args:
        email: The target person's email address.
        first_name: The person's first name.
        last_name: The person's last name.
        message: Optional personalized message (max 300 characters).

    Returns confirmation that the invitation was sent.
    """
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        result = await plugin.send_invitation_by_email(
            email=email,
            first_name=first_name,
            last_name=last_name,
            message=message or None,
        )
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_get_received_invitations(
    start: int = 0, count: int = 20
) -> str:
    """Get pending received LinkedIn connection invitations.

    Args:
        start: Pagination offset (default 0).
        count: Number of invitations to return (max 50, default 20).

    Returns a list of received invitation requests with sender info.
    """
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        result = await plugin.get_received_invitations(start=start, count=count)
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_get_sent_invitations(
    start: int = 0, count: int = 20
) -> str:
    """Get sent LinkedIn connection invitations and their status.

    Args:
        start: Pagination offset (default 0).
        count: Number of invitations to return (max 50, default 20).

    Returns a list of sent invitations with acceptance status.
    """
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        result = await plugin.get_sent_invitations(start=start, count=count)
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_accept_invitation(invitation_urn: str) -> str:
    """Accept a received LinkedIn connection invitation.

    Args:
        invitation_urn: The invitation URN (e.g., urn:li:invitation:123456).

    Returns confirmation that the invitation was accepted.
    """
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        result = await plugin.accept_invitation(invitation_urn)
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_ignore_invitation(invitation_urn: str) -> str:
    """Ignore (reject) a received LinkedIn connection invitation.

    Args:
        invitation_urn: The invitation URN to ignore.

    Returns confirmation that the invitation was ignored.
    """
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        result = await plugin.ignore_invitation(invitation_urn)
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


@mcp.tool()
async def linkedin_withdraw_invitation(invitation_urn: str) -> str:
    """Withdraw a sent LinkedIn connection invitation.

    Args:
        invitation_urn: The invitation URN to withdraw.

    Can only withdraw invitations that haven't been accepted yet.
    Returns confirmation that the invitation was withdrawn.
    """
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        result = await plugin.withdraw_invitation(invitation_urn)
        return _format_result(result)
    except Exception as e:
        return _error_response(e)


# ===========================================================================
#  RESOURCES
# ===========================================================================


@mcp.resource("linkedin://status")
def get_status() -> str:
    """Get the current LinkedIn MCP server status and authentication state."""
    return json.dumps({
        "server": "LinkedIn MCP Server",
        "version": "1.0.0",
        "authenticated": auth_manager.is_authenticated(),
        "api_version": settings.linkedin_api_version,
        "available_tools": {
            "auth": ["linkedin_auth_status", "linkedin_get_auth_url"],
            "profiles": [
                "linkedin_get_my_profile",
                "linkedin_get_my_profile_details",
                "linkedin_get_profile",
                "linkedin_get_connections",
                "linkedin_search_people",
                "linkedin_search_connections",
            ],
            "posts": [
                "linkedin_create_text_post",
                "linkedin_create_link_post",
                "linkedin_create_image_post",
                "linkedin_get_my_posts",
                "linkedin_get_post",
                "linkedin_delete_post",
                "linkedin_reshare_post",
            ],
            "invitations": [
                "linkedin_send_invitation",
                "linkedin_send_invitation_by_email",
                "linkedin_get_received_invitations",
                "linkedin_get_sent_invitations",
                "linkedin_accept_invitation",
                "linkedin_ignore_invitation",
                "linkedin_withdraw_invitation",
            ],
        },
    }, indent=2)


# ===========================================================================
#  PROMPTS
# ===========================================================================


@mcp.prompt()
def linkedin_post_assistant() -> str:
    """A prompt for helping users create engaging LinkedIn posts."""
    return (
        "You are a LinkedIn content assistant. Help the user craft engaging "
        "LinkedIn posts. Ask about:\n"
        "1. The topic or message they want to share\n"
        "2. Their target audience\n"
        "3. Whether they want to include links, images, or hashtags\n"
        "4. The desired tone (professional, casual, thought leadership)\n\n"
        "Then use the linkedin_create_text_post or linkedin_create_link_post "
        "tool to publish the post. Always suggest relevant hashtags and "
        "format the post for maximum engagement."
    )


@mcp.prompt()
def linkedin_network_assistant() -> str:
    """A prompt for helping users grow their LinkedIn network."""
    return (
        "You are a LinkedIn networking assistant. Help the user:\n"
        "1. Search for relevant people using linkedin_search_people\n"
        "2. Review their connections with linkedin_get_connections\n"
        "3. Send personalized connection invitations using linkedin_send_invitation\n\n"
        "Always suggest personalized messages for invitations to improve "
        "acceptance rates. Help craft messages that reference shared interests, "
        "mutual connections, or professional relevance."
    )


# ===========================================================================
#  ENTRY POINT
# ===========================================================================


def main():
    """Run the MCP server using stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
