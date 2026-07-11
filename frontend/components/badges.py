"""Freshness and status badges for dashboard metrics."""

from __future__ import annotations

import streamlit as st

FRESHNESS_LABELS = {
    "fresh": ("Fresh feed", "green"),
    "delayed": ("Delayed feed", "orange"),
    "stale": ("Stale feed", "red"),
}

STATUS_LABELS = {
    "healthy": ("Healthy", "green"),
    "pressure": ("Pressure", "orange"),
    "critical": ("Critical", "red"),
}


def render_freshness_badge(freshness: str) -> None:
    """Render a freshness badge for one metric."""

    label, color = FRESHNESS_LABELS.get(
        freshness,
        ("Unknown freshness", "gray"),
    )
    st.badge(label, color=color)


def render_status_badge(status: str) -> None:
    """Render a provider status badge."""

    label, color = STATUS_LABELS.get(
        status,
        ("Unknown status", "gray"),
    )
    st.badge(label, color=color)
