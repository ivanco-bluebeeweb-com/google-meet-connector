"""Google Meet Connector declaration and unified OAuth configuration."""

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "google-meet-connector",
    version="0.1.0",
    display_name="Google Meet Connector",
    description=(
        "Connect your own Google account to create and manage Google Meet "
        "spaces, review conference records (participants, sessions), "
        "recordings and transcripts (Workspace Business/Enterprise plans), "
        "and create Calendar events with an automatic Meet link."
    ),
    icon="icon.svg",
    capabilities=["google-meet:read", "google-meet:write"],
    actions_explicit=True,
)

chat = ChatExtension(
    ext,
    tool_name="google_meet",
    description=(
        "Google Meet Connector -- connect a Google account, create/manage "
        "Meet spaces, list conference records/participants, list "
        "recordings/transcripts, and create Calendar events with a Meet "
        "link attached."
    ),
)

# Meet API + Calendar (for conferenceData Meet-link creation) + basic
# identity. Read scopes cover spaces/records/recordings/transcripts;
# calendar.events is needed to create Meet-linked Calendar events.
ext.oauth(
    "google",
    collection="google_meet_accounts",
    scopes=[
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/meetings.space.created",
        "https://www.googleapis.com/auth/meetings.space.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ],
)

# Developer-owned OAuth app credentials. They are set once in the Developer
# Portal and are never shown to end users.
ext.secret(
    "google_client_id",
    "Google OAuth client ID for Google Meet Connector.",
    required=True,
    scope="app",
)(lambda: None)
ext.secret(
    "google_client_secret",
    "Google OAuth client secret for Google Meet Connector.",
    required=True,
    scope="app",
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Fast configuration health; no third-party call."""
    try:
        page = await ctx.store.query("google_meet_accounts", limit=1)
        count = len(page.data)
    except Exception:
        count = 0
    return {
        "healthy": count > 0,
        "accounts_configured": count,
        "detail": "Google account connected." if count else "No Google account connected yet.",
        "version": "0.1.0",
    }
