"""Google Meet Connector panels.

SIDEBAR CONTENT -- NO CARDS ANYWHERE, per ~/UI_INTERFACE_STANDARD.md's
"left sidebar, no decorated cards" rule. Every section is a plain
ui.Stack, stacked vertically and left-aligned, no Card border/background/
shadow. Disconnect lives only in "App settings" (panels_settings.py). The
one secondary "App settings" button is always the LAST element at the
bottom of the sidebar.

OAuth-based connect flow (like Google Drive Connector): no manual credential
form -- a single "Continue with Google" button opens ctx.oauth_authorize_url.
"""
from __future__ import annotations

from imperal_sdk import ui

import accounts as ac
from app import ext


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", full_width=True,
        icon="Settings", on_click=ui.Call("__panel__meet_settings"),
    )


async def _oauth_button(ctx, label: str, login_hint: str = "") -> ui.UINode:
    try:
        url = await ctx.oauth_authorize_url("google", login_hint=login_hint or None)
    except Exception:
        url = ""
    if url:
        return ui.Button(label, icon="ExternalLink", full_width=True, on_click=ui.Open(url))
    return ui.Button("Open connection setup", icon="Settings", full_width=True,
                      on_click=ui.Call("__panel__meet_settings"))


@ext.panel("meet_sidebar", slot="left", title="Google Meet")
async def meet_sidebar(ctx, **kwargs) -> ui.UINode:
    docs = await ac.all_accounts(ctx)
    if not docs:
        connect_btn = await _oauth_button(ctx, "Continue with Google")
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Empty(message="No Google account connected yet."),
            connect_btn,
            ui.Divider(),
            _settings_button(),
        ])

    rows: list[ui.UINode] = []
    for d in docs:
        email = ac.account_email(d) or ac.account_label(d)
        broken = ac.identity_missing(d)
        settings = await ac.setting(ctx, email) if email else {}
        has_error = broken or settings.get("state") == "error"
        subtitle = "Needs reconnecting" if has_error else "Connected"
        rows.append(ui.ListItem(id=d.id, title=email, subtitle=subtitle,
                                 icon="AlertTriangle" if has_error else "CheckCircle"))
        if has_error:
            rows.append(await _oauth_button(ctx, "Reconnect this account", login_hint=email))

    add_btn = await _oauth_button(ctx, "Connect another account")
    return ui.Stack(direction="v", gap=2, align="stretch", children=[
        *rows,
        ui.Divider(),
        add_btn,
        ui.Divider(),
        _settings_button(),
    ])
