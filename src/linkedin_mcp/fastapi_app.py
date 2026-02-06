"""FastAPI application for LinkedIn OAuth2 authentication and REST API.

Provides:
- OAuth2 login/callback endpoints for LinkedIn authentication
- REST API endpoints that proxy to LinkedIn API via plugins
- Health check and status endpoints
- **Remote MCP endpoint at /mcp for ChatGPT Enterprise (No Auth connector)**

Run with: uvicorn linkedin_mcp.fastapi_app:app --reload
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from linkedin_mcp.auth import LinkedInAuth
from linkedin_mcp.config import Settings, TokenStore, get_settings, get_token_store
from linkedin_mcp.linkedin_client import LinkedInAPIError, LinkedInClient
from linkedin_mcp.plugins.invitations import InvitationPlugin
from linkedin_mcp.plugins.posts import PostPlugin
from linkedin_mcp.plugins.profiles import ProfilePlugin
from linkedin_mcp.session_store import SessionStore

logger = logging.getLogger("linkedin_mcp.fastapi")

# ---------------------------------------------------------------------------
# Config / stores (created before the app so they can be referenced everywhere)
# ---------------------------------------------------------------------------

settings: Settings = get_settings()
token_store: TokenStore = get_token_store(settings)
auth = LinkedInAuth(settings, token_store)

# Multi-user SQLite store (ChatGPT POC)
session_db = SessionStore(settings.db_path)

# ---------------------------------------------------------------------------
# Remote MCP server (created early so we can wire the lifespan)
# ---------------------------------------------------------------------------

remote_mcp = FastMCP(
    "LinkedIn MCP (ChatGPT POC)",
    instructions=(
        "LinkedIn integration via MCP. "
        "If any tool returns a login_required error, ask the user to open the "
        "provided URL in their browser to authenticate with LinkedIn, then retry."
    ),
    stateless_http=True,
    streamable_http_path="/",
)

# Calling streamable_http_app() initializes the session_manager lazily
_mcp_starlette_app = remote_mcp.streamable_http_app()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Run the MCP session manager's task group alongside FastAPI."""
    async with remote_mcp.session_manager.run():
        logger.info("MCP session manager started")
        yield
    logger.info("MCP session manager stopped")


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="LinkedIn MCP API",
    description="FastAPI server for LinkedIn API - Profiles, Posts, Invitations",
    version="1.0.0",
    lifespan=_lifespan,
)

# Signed-cookie session middleware (browser sessions for OAuth flow)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)


def _get_client() -> LinkedInClient:
    """Build an authenticated LinkedIn API client or raise 401."""
    token = auth.get_access_token()
    return LinkedInClient(settings, token)


def _get_client_for_user(user_id: str | None = None) -> LinkedInClient:
    """Build an authenticated LinkedIn client from SQLite (multi-user POC).

    If *user_id* is ``None``, falls back to the most recent active token.
    Raises ``ValueError`` when no valid token is found.
    """
    tok = session_db.get_token(user_id) if user_id else session_db.get_active_token()
    if tok is None or tok["access_token"] is None:
        raise ValueError(
            "Not authenticated with LinkedIn. "
            f"Open this URL to connect: {settings.base_url}/auth/login"
        )
    return LinkedInClient(settings, tok["access_token"])


def _handle_api_error(e: LinkedInAPIError) -> None:
    raise HTTPException(
        status_code=e.status_code,
        detail={"message": e.message, "details": e.details},
    )


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
    """Landing page with auth status, ChatGPT connector setup guide."""
    active = session_db.get_active_token()
    authenticated = active is not None
    status_text = "Authenticated" if authenticated else "Not authenticated"
    user_info = ""
    if active:
        exp = active.get("expires_at")
        exp_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(exp)) if exp else "unknown"
        user_info = f"<p>User: <code>{active['user_id']}</code> — Token expires: {exp_str}</p>"

    return f"""
    <html>
    <head><title>LinkedIn MCP — ChatGPT POC</title>
    <style>
      body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; }}
      code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }}
      pre  {{ background: #f0f0f0; padding: 12px; border-radius: 6px; overflow-x: auto; }}
      .status {{ padding: 8px 16px; border-radius: 6px; display: inline-block; }}
      .ok  {{ background: #d4edda; color: #155724; }}
      .no  {{ background: #f8d7da; color: #721c24; }}
      a {{ color: #0a66c2; }}
    </style>
    </head>
    <body>
    <h1>LinkedIn MCP Server — ChatGPT POC</h1>

    <h2>1. Status</h2>
    <p class="status {'ok' if authenticated else 'no'}">LinkedIn: <strong>{status_text}</strong></p>
    {user_info}
    {'<p><a href="/auth/login">&#x1f517; Login with LinkedIn</a></p>' if not authenticated else
     '<p><a href="/auth/logout">Logout</a></p>'}

    <h2>2. Connect ChatGPT</h2>
    <ol>
      <li>In ChatGPT (Developer mode) &rarr; <em>Add MCP Connector</em></li>
      <li>URL: <code>{settings.base_url}/mcp</code></li>
      <li>Auth: <strong>No Auth</strong></li>
    </ol>

    <h2>3. Authenticate LinkedIn</h2>
    <p>Open <a href="{settings.base_url}/auth/login">{settings.base_url}/auth/login</a> in your browser
       and authorize the app. Then go back to ChatGPT and use the tools.</p>

    <h2>4. Debug</h2>
    <ul>
      <li><a href="/me">/me</a> — Current session &amp; token info</li>
      <li><a href="/auth/status">/auth/status</a> — Auth status (JSON)</li>
      <li><a href="/health">/health</a> — Health check</li>
      <li><a href="/docs">/docs</a> — Swagger API docs</li>
    </ul>

    <h2>5. Available MCP Tools</h2>
    <ul>
      <li><code>get_profile</code> — Get your LinkedIn profile</li>
      <li><code>list_connections</code> — List your 1st-degree connections</li>
      <li><code>create_post</code> — Create a text post on LinkedIn</li>
      <li><code>search_people</code> — Search for people by keywords</li>
    </ul>
    </body></html>
    """


@app.get("/auth/login")
async def login(request: Request):
    """Redirect user to LinkedIn authorization page."""
    if not settings.linkedin_client_id:
        raise HTTPException(
            status_code=500,
            detail="LINKEDIN_CLIENT_ID not configured. Set it in .env file.",
        )
    url = auth.get_authorization_url()
    logger.info("OAuth login initiated, redirecting to LinkedIn")
    return RedirectResponse(url=url)


@app.get("/auth/callback")
async def callback(request: Request, code: str = Query(...), state: str = Query("")):
    """Handle LinkedIn OAuth2 callback with authorization code.

    Exchanges the code for an access token, fetches the user's profile,
    and stores tokens in both the legacy JSON store and the new SQLite store.
    """
    try:
        token_data = await auth.exchange_code_for_token(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 5184000)

    # Fetch LinkedIn user info to get a stable user_id
    try:
        client = LinkedInClient(settings, access_token)
        user_info = await client.get_current_user()
        user_id = user_info.get("sub", "unknown")
    except Exception:
        user_id = "unknown"

    # Store in SQLite (multi-user)
    session_db.store_token(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )

    # Store user_id in browser session cookie
    request.session["user_id"] = user_id

    logger.info("OAuth callback success for user_id=%s", user_id)

    return HTMLResponse(f"""
    <html>
    <head><title>Auth Success</title>
    <style>
      body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; }}
      .ok {{ background: #d4edda; color: #155724; padding: 16px; border-radius: 6px; }}
    </style>
    </head>
    <body>
    <div class="ok">
      <h1>Authentication Successful</h1>
      <p>User: <code>{user_id}</code></p>
      <p>Token expires in: {expires_in} seconds</p>
      <p>You can now go back to ChatGPT and use the LinkedIn tools.</p>
    </div>
    <p><a href="/">Back to home</a> | <a href="/me">Check session</a></p>
    </body></html>
    """)


@app.get("/auth/status")
async def auth_status():
    """Check current authentication status (both legacy + SQLite)."""
    active = session_db.get_active_token()
    return {
        "authenticated_legacy": auth.is_authenticated(),
        "authenticated_sqlite": active is not None,
        "has_refresh_token": token_store.refresh_token is not None,
        "active_user_id": active["user_id"] if active else None,
    }


@app.post("/auth/logout")
async def logout_post(request: Request):
    """Clear stored tokens (POST)."""
    user_id = request.session.get("user_id")
    if user_id:
        session_db.delete_token(user_id)
    auth.logout()
    request.session.clear()
    return {"message": "Logged out successfully"}


@app.get("/auth/logout")
async def logout_get(request: Request):
    """Clear stored tokens and redirect to home (GET for browser use)."""
    user_id = request.session.get("user_id")
    if user_id:
        session_db.delete_token(user_id)
    auth.logout()
    request.session.clear()
    return RedirectResponse(url="/")


# ---------------------------------------------------------------------------
# /me — Debug session info
# ---------------------------------------------------------------------------


@app.get("/me")
async def me(request: Request):
    """Return current session and token status (debug endpoint)."""
    user_id = request.session.get("user_id")
    tok = session_db.get_token(user_id) if user_id else None
    if tok:
        exp = tok.get("expires_at")
        return {
            "logged_in": True,
            "user_id": user_id,
            "token_expires_at": exp,
            "token_expired": time.time() > exp if exp else False,
            "created_at": tok.get("created_at"),
            "has_refresh_token": tok.get("refresh_token") is not None,
        }
    return {
        "logged_in": False,
        "message": f"Open {settings.base_url}/auth/login to connect your LinkedIn account.",
    }


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


# ===========================================================================
# Remote MCP tools for ChatGPT Enterprise (No Auth connector)
# ===========================================================================
#
# The remote_mcp FastMCP instance is defined at the top of this module and
# mounted at /mcp via StreamableHTTP.  The original mcp_server.py (stdio)
# for Claude Desktop is untouched.
# ===========================================================================

BASE_URL = settings.base_url


def _auth_guard() -> LinkedInClient:
    """Return an authenticated client or raise with a helpful login message."""
    return _get_client_for_user()


def _mcp_format(data: Any) -> str:
    if isinstance(data, dict):
        return json.dumps(data, indent=2, ensure_ascii=False)
    return str(data)


def _mcp_login_error() -> str:
    return json.dumps(
        {
            "error": True,
            "login_required": True,
            "message": (
                "You are not authenticated with LinkedIn. "
                "Please open the following URL in your browser to connect your account:"
            ),
            "login_url": f"{BASE_URL}/auth/login",
        },
        indent=2,
    )


def _mcp_error(e: Exception) -> str:
    if isinstance(e, LinkedInAPIError):
        return json.dumps(
            {"error": True, "status_code": e.status_code, "message": e.message, "details": e.details},
            indent=2,
            ensure_ascii=False,
        )
    return json.dumps({"error": True, "message": str(e)}, indent=2, ensure_ascii=False)


# ---- Tool: get_profile ----


@remote_mcp.tool()
async def get_profile() -> str:
    """Get the authenticated LinkedIn user's profile.

    Returns the user's name, email, profile picture, and locale information.
    Requires the user to have authenticated via /auth/login first.
    """
    try:
        client = _auth_guard()
        plugin = ProfilePlugin(client)
        result = await plugin.get_my_profile()
        return _mcp_format(result)
    except ValueError:
        return _mcp_login_error()
    except Exception as e:
        return _mcp_error(e)


# ---- Tool: list_connections ----


@remote_mcp.tool()
async def list_connections(start: int = 0, count: int = 50) -> str:
    """Get the authenticated user's 1st-degree LinkedIn connections.

    Args:
        start: Pagination offset (default 0).
        count: Number of connections to return (max 50).

    Returns a paginated list of connection URNs.
    """
    try:
        client = _auth_guard()
        plugin = ProfilePlugin(client)
        result = await plugin.get_connections(start=start, count=count)
        return _mcp_format(result)
    except ValueError:
        return _mcp_login_error()
    except Exception as e:
        return _mcp_error(e)


# ---- Tool: create_post ----


@remote_mcp.tool()
async def create_post(text: str, visibility: str = "PUBLIC") -> str:
    """Create a text post on LinkedIn.

    Args:
        text: The post content. Supports hashtags (#topic), mentions, line breaks.
        visibility: Who can see the post — PUBLIC, CONNECTIONS, or LOGGED_IN.

    Returns the post URN on success.
    """
    try:
        client = _auth_guard()
        plugin = PostPlugin(client)
        result = await plugin.create_text_post(text=text, visibility=visibility)
        return _mcp_format(result)
    except ValueError:
        return _mcp_login_error()
    except Exception as e:
        return _mcp_error(e)


# ---- Tool: search_people ----


@remote_mcp.tool()
async def search_people(keywords: str, start: int = 0, count: int = 10) -> str:
    """Search for LinkedIn people/profiles by keywords.

    Args:
        keywords: Search query — name, job title, company, skill, etc.
        start: Pagination offset (default 0).
        count: Number of results to return (max 50, default 10).

    Returns matching profiles with basic information.
    """
    try:
        client = _auth_guard()
        plugin = ProfilePlugin(client)
        result = await plugin.search_people_by_keyword(
            keywords=keywords, start=start, count=count
        )
        return _mcp_format(result)
    except ValueError:
        return _mcp_login_error()
    except Exception as e:
        return _mcp_error(e)


# Mount the pre-built MCP Starlette app at /mcp
app.mount("/mcp", _mcp_starlette_app)

logger.info("Remote MCP endpoint mounted at /mcp (StreamableHTTP, No Auth)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Entry point for running the FastAPI server."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logger.info("Starting LinkedIn MCP API — BASE_URL=%s", settings.base_url)
    uvicorn.run(
        "linkedin_mcp.fastapi_app:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
