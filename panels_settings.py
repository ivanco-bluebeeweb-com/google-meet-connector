"""Google Meet Connector -- App settings panel."""
from __future__ import annotations

from imperal_sdk import ui

import accounts as ac
from app import ext


@ext.panel("meet_settings", slot="center", title="Google Meet settings", icon="Settings", center_overlay=True)
async def meet_settings(ctx, **kwargs) -> ui.UINode:
    docs = await ac.all_accounts(ctx)
    if not docs:
        try:
            url = await ctx.oauth_authorize_url("google")
        except Exception:
            url = ""
        children = [ui.Text("No Google account connected yet.", variant="body")]
        if url:
            children.append(ui.Button("Continue with Google", icon="ExternalLink", on_click=ui.Open(url)))
        return ui.Stack(direction="v", gap=3, align="stretch", children=children)

    rows = []
    for d in docs:
        email = ac.account_email(d) or ac.account_label(d)
        rows.append(ui.Stack(direction="h", gap=2, align="center", children=[
            ui.Text(email, variant="body"),
            ui.Button("Disconnect", variant="destructive", on_click=ui.Call("disconnect_account", account_id=d.id)),
        ]))
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Connected accounts", level=2),
        *rows,
        ui.Divider(),
        ui.Text(
            "How do I connect? Sign in with a Google account. Meet space "
            "creation/reading needs the Meet API scopes; creating Calendar "
            "events with a Meet link needs Calendar access. Recordings and "
            "transcripts require a Google Workspace Business/Enterprise plan "
            "with the relevant Meet add-on -- personal Gmail accounts and "
            "some Workspace tiers will not have those features available.",
            variant="caption",
        ),
    ])
