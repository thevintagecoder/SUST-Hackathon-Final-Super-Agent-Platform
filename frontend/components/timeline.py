"""Vertical timeline component for case management."""

from __future__ import annotations

import streamlit as st


def render_timeline(events: list[dict]) -> None:
    """Render an append-only case timeline."""

    if not events:
        st.info("No timeline events recorded yet.")
        return

    for event in events:
        title = event["event"].replace("_", " ").title()
        st.markdown(f"**{title}**")
        st.caption(f"{event['at']} · {event['actor']}")
        st.write(event["note"])
        st.divider()
