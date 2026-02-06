"""FastAPI application for LinkedIn OAuth2 authentication and REST API.

Provides:
- OAuth2 login/callback endpoints for LinkedIn authentication
- REST API endpoints that proxy to LinkedIn API via plugins
- Health check and status endpoints

Run with: uvicorn linkedin_mcp.fastapi_app:app --reload
"""

from __future__ import annotations

import json
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from linkedin_mcp.auth import LinkedInAuth
from linkedin_mcp.config import Settings, TokenStore, get_settings, get_token_store
from linkedin_mcp.linkedin_client import LinkedInAPIError, LinkedInClient
from linkedin_mcp.plugins.invitations import InvitationPlugin
from linkedin_mcp.plugins.posts import PostPlugin
from linkedin_mcp.plugins.profiles import ProfilePlugin

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="LinkedIn MCP API",
    description="FastAPI server for LinkedIn API - Profiles, Posts, Invitations",
    version="1.0.0",
)

settings: Settings = get_settings()
token_store: TokenStore = get_token_store(settings)
auth = LinkedInAuth(settings, token_store)


def _get_client() -> LinkedInClient:
    """Build an authenticated LinkedIn API client or raise 401."""
    token = auth.get_access_token()
    return LinkedInClient(settings, token)


def _handle_api_error(e: LinkedInAPIError) -> None:
    raise HTTPException(status_code=e.status_code, detail={"message": e.message, "details": e.details})


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class TextPostRequest(BaseModel):
    text: str
    visibility: str = "PUBLIC"


class LinkPostRequest(BaseModel):
    text: str
    link_url: str
    link_title: str | None = None
    link_description: str | None = None
    visibility: str = "PUBLIC"


class ImagePostRequest(BaseModel):
    text: str
    image_path: str
    alt_text: str = ""
    visibility: str = "PUBLIC"


class ReshareRequest(BaseModel):
    original_post_urn: str
    text: str = ""
    visibility: str = "PUBLIC"


class InvitationRequest(BaseModel):
    person_id: str
    message: str | None = None


class EmailInvitationRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    message: str | None = None


class InvitationActionRequest(BaseModel):
    invitation_urn: str


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page with auth status and links."""
    authenticated = auth.is_authenticated()
    status = "Authenticated" if authenticated else "Not authenticated"
    login_link = '<a href="/auth/login">Login with LinkedIn</a>' if not authenticated else ""
    return f"""
    <html><body>
    <h1>LinkedIn MCP Server</h1>
    <p>Status: <strong>{status}</strong></p>
    {login_link}
    <hr>
    <p><a href="/docs">API Documentation (Swagger)</a></p>
    </body></html>
    """


@app.get("/auth/login")
async def login():
    """Redirect user to LinkedIn authorization page."""
    if not settings.linkedin_client_id:
        raise HTTPException(
            status_code=500,
            detail="LINKEDIN_CLIENT_ID not configured. Set it in .env file.",
        )
    url = auth.get_authorization_url()
    return RedirectResponse(url=url)


@app.get("/auth/callback")
async def callback(code: str = Query(...), state: str = Query("")):
    """Handle LinkedIn OAuth2 callback with authorization code.

    Exchanges the code for an access token and stores it.
    """
    try:
        token_data = await auth.exchange_code_for_token(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")

    return HTMLResponse(f"""
    <html><body>
    <h1>Authentication Successful</h1>
    <p>Access token stored. You can now use the API.</p>
    <p>Token expires in: {token_data.get('expires_in', 'unknown')} seconds</p>
    <p><a href="/docs">Go to API docs</a></p>
    </body></html>
    """)


@app.get("/auth/status")
async def auth_status():
    """Check current authentication status."""
    return {
        "authenticated": auth.is_authenticated(),
        "has_refresh_token": token_store.refresh_token is not None,
    }


@app.post("/auth/logout")
async def logout():
    """Clear stored tokens."""
    auth.logout()
    return {"message": "Logged out successfully"}


# ---------------------------------------------------------------------------
# Profile endpoints
# ---------------------------------------------------------------------------

@app.get("/api/profiles/me")
async def get_my_profile():
    """Get the authenticated user's profile."""
    try:
        client = _get_client()
        plugin = ProfilePlugin(client)
        return await plugin.get_my_profile()
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/profiles/me/details")
async def get_my_profile_details():
    """Get detailed profile of the authenticated user."""
    try:
        client = _get_client()
        plugin = ProfilePlugin(client)
        return await plugin.get_my_profile_details()
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/profiles/{person_id}")
async def get_profile(person_id: str):
    """Get a profile by person ID."""
    try:
        client = _get_client()
        plugin = ProfilePlugin(client)
        return await plugin.get_profile_by_id(person_id)
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/profiles/connections")
async def get_connections(start: int = 0, count: int = 50):
    """Get 1st-degree connections."""
    try:
        client = _get_client()
        plugin = ProfilePlugin(client)
        return await plugin.get_connections(start=start, count=count)
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/profiles/search")
async def search_people(keywords: str = Query(...), start: int = 0, count: int = 10):
    """Search for people by keywords."""
    try:
        client = _get_client()
        plugin = ProfilePlugin(client)
        return await plugin.search_people_by_keyword(
            keywords=keywords, start=start, count=count
        )
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ---------------------------------------------------------------------------
# Post endpoints
# ---------------------------------------------------------------------------

@app.post("/api/posts/text")
async def create_text_post(req: TextPostRequest):
    """Create a text-only post."""
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        return await plugin.create_text_post(text=req.text, visibility=req.visibility)
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/posts/link")
async def create_link_post(req: LinkPostRequest):
    """Create a post with a link/article attachment."""
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        return await plugin.create_post_with_link(
            text=req.text,
            link_url=req.link_url,
            link_title=req.link_title,
            link_description=req.link_description,
            visibility=req.visibility,
        )
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/posts/image")
async def create_image_post(req: ImagePostRequest):
    """Create a post with an image attachment."""
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        return await plugin.create_post_with_image(
            text=req.text,
            image_path=req.image_path,
            alt_text=req.alt_text,
            visibility=req.visibility,
        )
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/posts/reshare")
async def reshare_post(req: ReshareRequest):
    """Reshare an existing post."""
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        return await plugin.create_reshare(
            original_post_urn=req.original_post_urn,
            text=req.text,
            visibility=req.visibility,
        )
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/posts/mine")
async def get_my_posts(count: int = 10):
    """Get the authenticated user's posts."""
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        return await plugin.get_my_posts(count=count)
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/posts/{post_urn:path}")
async def get_post(post_urn: str):
    """Get a specific post by URN."""
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        return await plugin.get_post(post_urn)
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.delete("/api/posts/{post_urn:path}")
async def delete_post(post_urn: str):
    """Delete a post by URN."""
    try:
        client = _get_client()
        plugin = PostPlugin(client)
        await plugin.delete_post(post_urn)
        return {"message": "Post deleted successfully"}
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ---------------------------------------------------------------------------
# Invitation endpoints
# ---------------------------------------------------------------------------

@app.post("/api/invitations/send")
async def send_invitation(req: InvitationRequest):
    """Send a connection invitation to a person by ID."""
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        return await plugin.send_invitation(
            person_id=req.person_id, message=req.message
        )
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/invitations/send-by-email")
async def send_invitation_by_email(req: EmailInvitationRequest):
    """Send a connection invitation using an email address."""
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        return await plugin.send_invitation_by_email(
            email=req.email,
            first_name=req.first_name,
            last_name=req.last_name,
            message=req.message,
        )
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/invitations/received")
async def get_received_invitations(start: int = 0, count: int = 20):
    """Get pending received invitations."""
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        return await plugin.get_received_invitations(start=start, count=count)
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/invitations/sent")
async def get_sent_invitations(start: int = 0, count: int = 20):
    """Get sent invitations."""
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        return await plugin.get_sent_invitations(start=start, count=count)
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/invitations/accept")
async def accept_invitation(req: InvitationActionRequest):
    """Accept a received invitation."""
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        return await plugin.accept_invitation(req.invitation_urn)
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/invitations/ignore")
async def ignore_invitation(req: InvitationActionRequest):
    """Ignore a received invitation."""
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        return await plugin.ignore_invitation(req.invitation_urn)
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/invitations/withdraw")
async def withdraw_invitation(req: InvitationActionRequest):
    """Withdraw a sent invitation."""
    try:
        client = _get_client()
        plugin = InvitationPlugin(client)
        return await plugin.withdraw_invitation(req.invitation_urn)
    except LinkedInAPIError as e:
        _handle_api_error(e)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


def main():
    """Entry point for running the FastAPI server."""
    uvicorn.run(
        "linkedin_mcp.fastapi_app:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
