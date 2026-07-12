"""Cases — alerts inbox and support-request workflow."""

from __future__ import annotations

import streamlit as st

from frontend.api.client import BackendClient
from frontend.components.common import safety_notice
from frontend.views.alerts import render_alerts
from frontend.views.support_requests import render_support_requests


def render_cases(client: BackendClient) -> None:
    """Render alert reviews and peer support coordination."""

    st.header("Cases")
    st.markdown(
        '<div class="section-intro">'
        "Human-owned workflows: review risk alerts, assign owners, "
        "then coordinate peer support — accept, escalate, resolve."
        "</div>",
        unsafe_allow_html=True,
    )
    safety_notice()

    tab_alerts, tab_support = st.tabs(
        ["Alert inbox", "Support requests"]
    )

    with tab_alerts:
        render_alerts(client)

    with tab_support:
        render_support_requests(client)
