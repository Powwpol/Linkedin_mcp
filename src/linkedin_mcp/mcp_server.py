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
from linkedin_mcp.skills.business_context import BusinessContext, load_business_context
from linkedin_mcp.skills.copywriting import CopywritingSkill
from linkedin_mcp.skills.content_strategy import ContentStrategySkill
from linkedin_mcp.skills.engagement import EngagementSkill
from linkedin_mcp.skills.neuromarketing import NeuroMarketingSkill

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
        "skills": {
            "neuromarketing": [
                "skill_neuro_post",
                "skill_neuro_catalog",
            ],
            "copywriting": [
                "skill_copywriting_post",
                "skill_copywriting_ab_test",
                "skill_copywriting_catalog",
            ],
            "engagement": [
                "skill_engagement_post",
                "skill_engagement_hooks",
                "skill_engagement_ctas",
            ],
            "content_strategy": [
                "skill_content_calendar",
                "skill_content_ideas",
            ],
            "business_context": [
                "skill_show_business_context",
            ],
        },
    }, indent=2)


# ===========================================================================
#  SKILLS - Neuro-marketing, Copywriting, Engagement, Strategy
# ===========================================================================


def _load_ctx(business_context: str = "") -> BusinessContext:
    """Load business context from explicit input or CLAUDE.md."""
    return load_business_context(business_context or None)


# --- Neuro-marketing tools ---


@mcp.tool()
def skill_neuro_post(
    topic: str,
    bias: str = "curiosity_gap",
    emotion: str = "educate",
    post_format: str = "story",
    business_context: str = "",
) -> str:
    """Generate a neuro-marketing optimized LinkedIn post prompt.

    Creates a detailed prompt applying neuroscience-backed persuasion
    principles (cognitive biases + emotional triggers) to write a
    high-engagement LinkedIn post.

    Args:
        topic: The subject of the post (e.g., "Why cold outreach is dead").
        bias: Cognitive bias to leverage. Options:
              - curiosity_gap: Information gap that forces engagement
              - loss_aversion: Frame around what the reader LOSES
              - social_proof: Show others already doing it
              - authority_bias: Position as expert with data
              - reciprocity: Give value before asking
              - anchoring: Use reference points for contrast
              - scarcity_fomo: Create authentic urgency
              - storytelling_arc: Narrative with neural coupling
        emotion: Emotional trigger. Options:
                 - inspire: Hope, admiration, pride
                 - educate: Curiosity, surprise, eureka
                 - provoke: Indignation, challenge beliefs
                 - connect: Belonging, empathy, shared experience
                 - activate: Urgency, motivation, push to act
        post_format: Post structure. Options:
                     - story: Narrative arc (situation > complication > resolution)
                     - list: Value list (reciprocity-driven)
                     - contrarian: Strong opposing take
                     - tutorial: Step-by-step how-to
                     - question: Open question (Zeigarnik effect)
        business_context: Optional business context override (markdown).
                          If empty, reads from CLAUDE.md automatically.

    Returns the complete prompt ready to generate the post.
    """
    ctx = _load_ctx(business_context)
    skill = NeuroMarketingSkill(ctx)
    return skill.generate_post_prompt(
        topic=topic, bias=bias, emotion=emotion, post_format=post_format
    )


@mcp.tool()
def skill_neuro_catalog() -> str:
    """Get the complete catalog of cognitive biases and emotional triggers.

    Returns all available neuro-marketing levers with descriptions,
    principles, hook examples, and usage recommendations.
    Use this to choose the best bias/emotion combo for a topic.
    """
    ctx = _load_ctx()
    skill = NeuroMarketingSkill(ctx)
    return skill.get_bias_catalog() + "\n\n---\n\n" + skill.get_emotion_catalog()


# --- Copywriting tools ---


@mcp.tool()
def skill_copywriting_post(
    topic: str,
    framework: str = "pas",
    tone: str = "",
    business_context: str = "",
) -> str:
    """Generate a LinkedIn post using a proven copywriting framework.

    Applies structured copywriting formulas to create persuasive posts
    with clear narrative flow and strong calls to action.

    Args:
        topic: The subject of the post.
        framework: Copywriting framework to apply. Options:
                   - aida: Attention > Interest > Desire > Action
                   - pas: Problem > Agitation > Solution
                   - bab: Before > After > Bridge
                   - 4ps: Promise > Picture > Proof > Push
                   - app: Agree > Promise > Preview
                   - slap: Stop > Look > Act > Purchase
        tone: Optional tone override (e.g., "Expert direct", "Pedagogue chaleureux").
              If empty, uses tone from CLAUDE.md business context.
        business_context: Optional business context override (markdown).

    Returns the complete prompt ready to generate the post.
    """
    ctx = _load_ctx(business_context)
    skill = CopywritingSkill(ctx)
    return skill.generate_copywriting_prompt(
        topic=topic, framework=framework, tone=tone or None
    )


@mcp.tool()
def skill_copywriting_ab_test(
    topic: str,
    framework_a: str = "pas",
    framework_b: str = "aida",
    business_context: str = "",
) -> str:
    """Generate two versions of a LinkedIn post for A/B testing.

    Creates two posts on the same topic using different copywriting
    frameworks so you can test which performs better.

    Args:
        topic: The subject of both posts.
        framework_a: First framework (pas, aida, bab, 4ps, app, slap).
        framework_b: Second framework (different from framework_a).
        business_context: Optional business context override.

    Returns prompts for both versions with comparison analysis.
    """
    ctx = _load_ctx(business_context)
    skill = CopywritingSkill(ctx)
    return skill.generate_ab_test_prompt(
        topic=topic, framework_a=framework_a, framework_b=framework_b
    )


@mcp.tool()
def skill_copywriting_catalog() -> str:
    """Get the complete catalog of copywriting frameworks.

    Returns all 6 frameworks with descriptions, step-by-step structures,
    ideal use cases, and example hooks.
    Use this to choose the best framework for your topic and goal.
    """
    ctx = _load_ctx()
    skill = CopywritingSkill(ctx)
    return skill.get_framework_catalog()


# --- Engagement tools ---


@mcp.tool()
def skill_engagement_post(
    topic: str,
    objective: str = "comments",
    hook_style: str = "",
    business_context: str = "",
) -> str:
    """Generate a LinkedIn post optimized for a specific engagement metric.

    Uses LinkedIn algorithm knowledge and proven engagement patterns
    to maximize a chosen metric (comments, saves, leads, shares, or profile visits).

    Args:
        topic: The subject of the post.
        objective: Engagement metric to optimize. Options:
                   - comments: Maximize meaningful comments (best for algo)
                   - saves: Maximize saves (reference content)
                   - leads: Generate qualified leads
                   - shares: Maximize shares (virality)
                   - profile_visits: Drive profile visits
        hook_style: Optional specific hook formula. Options:
                    - "Le Chiffre Choc"
                    - "L'Anti-Conseil"
                    - "La Confession"
                    - "La Question Impossible"
                    - "Le Comparatif Violent"
                    - "L'Enumeration Promise"
                    - "Le Dialogue Direct"
                    - "L'Observation Silencieuse"
                    If empty, auto-selects the best hook for the topic.
        business_context: Optional business context override.

    Returns the post prompt + first comment + response templates.
    """
    ctx = _load_ctx(business_context)
    skill = EngagementSkill(ctx)
    return skill.generate_engagement_prompt(
        topic=topic, objective=objective, hook_style=hook_style or None
    )


@mcp.tool()
def skill_engagement_hooks() -> str:
    """Get the complete catalog of LinkedIn hook formulas.

    Returns 8 proven hook formulas with effectiveness ratings,
    examples, and best use cases. Use this to pick the perfect
    scroll-stopping first line for your post.
    """
    ctx = _load_ctx()
    skill = EngagementSkill(ctx)
    return skill.get_hook_catalog()


@mcp.tool()
def skill_engagement_ctas() -> str:
    """Get the complete catalog of CTA strategies by objective.

    Returns call-to-action strategies organized by goal:
    comments, saves, leads, shares, profile visits.
    Each with specific techniques and wording examples.
    """
    ctx = _load_ctx()
    skill = EngagementSkill(ctx)
    return skill.get_cta_catalog()


# --- Content Strategy tools ---


@mcp.tool()
def skill_content_calendar(
    mode: str = "growth_mode",
    weeks: int = 1,
    business_context: str = "",
) -> str:
    """Generate a strategic LinkedIn content calendar.

    Creates a detailed weekly plan with post topics, hooks, formats,
    pillar rotation, and funnel stage targeting.

    Args:
        mode: Strategy mode. Options:
              - growth_mode: 5 posts/week for audience growth
              - authority_mode: 3 posts/week for expert positioning
              - lead_gen_mode: 4 posts/week for lead generation
        weeks: Number of weeks to plan (1-4).
        business_context: Optional business context override.

    Returns a complete calendar with hooks, angles, formats, CTAs,
    and first comments for every post.
    """
    ctx = _load_ctx(business_context)
    skill = ContentStrategySkill(ctx)
    return skill.generate_strategy_prompt(mode=mode, weeks=min(weeks, 4))


@mcp.tool()
def skill_content_ideas(
    pillar: str = "expertise",
    funnel_stage: str = "tofu",
    count: int = 10,
    business_context: str = "",
) -> str:
    """Brainstorm LinkedIn post ideas for a specific pillar and funnel stage.

    Generates targeted content ideas aligned with your business context,
    content pillars, and audience funnel position.

    Args:
        pillar: Content pillar to focus on. Options:
                - expertise: Technical know-how, tutorials
                - behind_the_scenes: Authenticity, backstage
                - industry_vision: Trends, predictions
                - social_proof: Results, testimonials
                - personal_brand: Values, convictions
                - curation: Resources, tools, recommendations
        funnel_stage: Audience targeting. Options:
                      - tofu: Top of funnel (awareness, reach)
                      - mofu: Middle of funnel (trust, authority)
                      - bofu: Bottom of funnel (conversion)
        count: Number of ideas to generate (1-20).
        business_context: Optional business context override.

    Returns ideas with hooks, angles, formats, and difficulty ratings.
    """
    ctx = _load_ctx(business_context)
    skill = ContentStrategySkill(ctx)
    return skill.generate_content_idea_prompt(
        pillar=pillar, funnel_stage=funnel_stage, count=min(count, 20)
    )


# --- Business Context tool ---


@mcp.tool()
def skill_show_business_context(business_context: str = "") -> str:
    """Show the current business context used by all skills.

    Displays the parsed business context from CLAUDE.md or the
    provided override. Useful for verifying that skills will use
    the correct brand, audience, and tone information.

    Args:
        business_context: Optional override. If empty, reads CLAUDE.md.

    Returns the formatted business context block.
    """
    ctx = _load_ctx(business_context)
    if not ctx.has_context():
        return (
            "Aucun contexte business charge.\n\n"
            "Pour personnaliser les skills, remplissez le fichier CLAUDE.md "
            "a la racine du projet avec vos informations business :\n"
            "- Identite (marque, secteur)\n"
            "- Proposition de valeur\n"
            "- Audience cible (ICP, douleurs)\n"
            "- Ton et style\n"
            "- Piliers de contenu\n"
            "- Objectifs LinkedIn\n\n"
            "Ou passez le contexte directement via le parametre business_context."
        )
    return ctx.to_prompt_block()


# ===========================================================================
#  PROMPTS (MCP prompt templates for AI agents)
# ===========================================================================


@mcp.prompt()
def linkedin_post_assistant() -> str:
    """Assistant for creating high-engagement LinkedIn posts with neuro-marketing."""
    ctx = _load_ctx()
    context_block = ctx.to_prompt_block() if ctx.has_context() else ""
    return f"""Tu es un expert en neuro-marketing et copywriting LinkedIn.
Tu aides l'utilisateur a creer des posts LinkedIn ultra-engageants.

{context_block}

## Ton processus

1. **Comprendre le sujet** : Demande le sujet/message principal
2. **Identifier l'objectif** : Leads ? Visibilite ? Autorite ? Communaute ?
3. **Choisir la strategie** :
   - Biais cognitif (curiosite, perte, preuve sociale, autorite, reciprocite)
   - Emotion ciblee (inspirer, eduquer, provoquer, connecter, activer)
   - Framework copywriting (AIDA, PAS, BAB, 4Ps, APP, SLAP)
   - Format (story, liste, contrarian, tutoriel, question)
4. **Generer le post** avec les tools skill_neuro_post ou skill_copywriting_post
5. **Optimiser l'engagement** avec skill_engagement_post si besoin
6. **Publier** avec linkedin_create_text_post ou linkedin_create_link_post

## Regles

- Jamais de post generique : toujours specifique au contexte business
- Toujours un hook en premiere ligne (pattern interrupt)
- Toujours un CTA en derniere ligne
- Toujours preparer le premier commentaire
- 1200-1500 caracteres, bien espace
- 3-5 hashtags
- Pas de liens externes dans le corps"""


@mcp.prompt()
def linkedin_network_assistant() -> str:
    """Assistant for growing LinkedIn network with personalized outreach."""
    ctx = _load_ctx()
    context_block = ctx.to_prompt_block() if ctx.has_context() else ""
    return f"""Tu es un expert en growth LinkedIn et networking strategique.

{context_block}

## Ton processus

1. **Definir la cible** : Qui l'utilisateur veut-il atteindre et pourquoi ?
2. **Rechercher** : Utilise linkedin_search_people pour trouver les bons profils
3. **Analyser** : Revise linkedin_get_connections pour le reseau existant
4. **Personnaliser** : Redige des messages d'invitation adaptes a chaque profil
5. **Envoyer** : Utilise linkedin_send_invitation avec le message personnalise

## Regles pour les messages d'invitation

- Max 300 caracteres (contrainte LinkedIn)
- Toujours personnaliser (nom, point commun, raison du contact)
- Pas de pitch dans l'invitation, juste la connexion
- Formules efficaces :
  * Point commun : "J'ai vu votre post sur [X], je travaille aussi sur [Y]"
  * Valeur : "Je partage regulierement du contenu sur [X], je pense que ca pourrait vous interesser"
  * Mutual : "Nous sommes tous les deux connectes a [nom], [raison]"
  * Direct : "Votre travail sur [X] m'interesse, j'aimerais echanger"

## Ne jamais :
- Envoyer des invitations en masse sans personnalisation
- Pitcher un produit dans le message d'invitation
- Envoyer plus de 20 invitations par jour"""


@mcp.prompt()
def linkedin_content_strategist() -> str:
    """Assistant for planning LinkedIn content strategy."""
    ctx = _load_ctx()
    context_block = ctx.to_prompt_block() if ctx.has_context() else ""
    return f"""Tu es un strategiste de contenu LinkedIn senior.

{context_block}

## Ton processus

1. **Audit** : Analyse le contexte business et les objectifs LinkedIn
2. **Piliers** : Definis ou ajuste les piliers de contenu
3. **Funnel** : Equilibre le contenu TOFU (40%) / MOFU (35%) / BOFU (25%)
4. **Calendrier** : Genere un plan avec skill_content_calendar
5. **Ideation** : Brainstorme des sujets avec skill_content_ideas
6. **Production** : Pour chaque post, utilise les skills neuro/copywriting

## Outils disponibles

- skill_content_calendar : Calendrier complet (growth / authority / lead gen)
- skill_content_ideas : Brainstorming d'idees par pilier et funnel stage
- skill_neuro_post : Generation neuro-marketing
- skill_copywriting_post : Generation avec frameworks de copywriting
- skill_engagement_post : Optimisation engagement
- skill_copywriting_ab_test : A/B test entre frameworks

## Principes

- Coherence : chaque post renforce le positionnement global
- Variete : alterner formats et tons pour eviter la lassitude
- Regularite : mieux vaut 3 posts/semaine constants que 7 puis 0
- Mesure : definir des KPIs clairs pour chaque type de contenu"""


# ===========================================================================
#  ENTRY POINT
# ===========================================================================


def main():
    """Run the MCP server using stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
