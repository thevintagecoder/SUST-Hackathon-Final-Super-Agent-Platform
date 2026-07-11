"""Metric card helpers for operations overview."""

from __future__ import annotations

import streamlit as st

from frontend.components.badges import render_freshness_badge, render_status_badge


def format_currency(amount: float) -> str:
    """Format one synthetic currency amount."""

    return f"{amount:,.2f}"


def render_shared_cash_card(shared_cash: dict) -> None:
    """Render shared physical cash separately from provider balances."""

    st.subheader("Shared physical cash")
    st.metric(
        label="Available shared cash",
        value=format_currency(shared_cash["amount"]),
    )
    render_freshness_badge(shared_cash["freshness"])
    st.caption(f"Last updated: {shared_cash['as_of']}")


def render_provider_card(provider: dict) -> None:
    """Render one provider balance card."""

    st.subheader(provider["code"])
    st.metric(
        label="Electronic balance",
        value=format_currency(provider["balance"]),
    )
    render_status_badge(provider["status"])
    render_freshness_badge(provider["freshness"])


def render_alert_summary(open_alerts: int, unacknowledged_alerts: int) -> None:
    """Render alert count summary metrics."""

    left, right = st.columns(2)
    with left:
        st.metric("Open alerts", open_alerts)
    with right:
        st.metric("Unacknowledged alerts", unacknowledged_alerts)
