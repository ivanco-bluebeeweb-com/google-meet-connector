# Google Meet Connector

Manage [Google Meet](https://developers.google.com/meet/api/guides/overview)
over the Meet REST API v2 plus Google Calendar v3: create and configure Meet
spaces (access type: open/trusted/restricted), end active conferences, list
conference records with their participants and participant sessions, list
recordings and transcripts (with transcript entries) for accounts on a
qualifying Google Workspace plan, and create/read/cancel Calendar events
with an automatic Meet link attached. Bring-your-own-account (BYOK) via
Google OAuth -- you connect your own Google account, every call runs
against your own Meet spaces and Calendar.

## Connecting

1. Click **Continue with Google** in the left-hand panel, or call
   `list_connections` from chat to check what's already connected.
2. Sign in and approve the requested scopes: Meet space creation/read
   access, and Calendar events (needed to create Meet-linked Calendar
   events). You can connect more than one Google account.
3. **Recordings and transcripts** are only available on Google Workspace
   Business Standard/Plus, Enterprise, or Education plans with Smart
   Meeting features enabled -- personal Gmail accounts and some Workspace
   tiers will not have this data, and the connector will say so plainly
   rather than silently returning nothing.
4. If a connected account starts erroring, "App settings" shows its status
   and a one-click Reconnect via the same Google OAuth screen.

## What you can do

- **Spaces**: create a Meet space with a chosen access type (OPEN/TRUSTED/
  RESTRICTED), read a space's join URL and current active conference, update
  its access-type configuration, or end its currently active conference.
- **Conference records**: list past conferences (optionally for one space),
  read one in full, and list its participants and each participant's
  individual join/leave sessions.
- **Recordings & transcripts**: list and read recordings and transcripts
  attached to a conference record, and read transcript entries (spoken text
  segments with speaker and timing) -- Workspace plan required.
- **Calendar integration**: create a Calendar event with an automatically
  attached Meet link (the practical way to schedule a meeting without full
  Meet API space management), read or cancel it.
- **Audit**: a one-glance usage report across recent conference records --
  meeting count, total participants, and average duration -- for a
  Workspace admin reviewing Meet usage.

## Notes

- Application-only access (service account + domain-wide delegation) is
  **not** used here; every action runs as the connected user's own OAuth
  identity, scoped to what that Google account itself can see.
- Google's Meet API is comparatively new (GA since 2024) -- some accounts,
  plans, or regions may not have every feature enabled yet. Errors say
  plainly when a feature needs a plan upgrade rather than guessing.
