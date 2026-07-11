"""Alert presentation with responsible decision-support language."""

from __future__ import annotations

import streamlit as st

from frontend.components.badges import render_freshness_badge


def format_confidence(confidence: float) -> str:
    """Format confidence as percentage text, not certainty."""

    return f"{confidence * 100:.0f}% confidence"


def render_alert_card(alert: dict) -> None:
    """Render one alert with evidence and safe next steps."""

    st.subheader(alert["title"])
    st.caption(
        f"Alert #{alert['id']} · {alert['severity'].title()} · "
        f"{alert['status'].replace('_', ' ').title()}"
    )
    st.write(alert["reason"])
    st.info(format_confidence(alert["confidence"]))
    st.warning(alert["uncertainty"])

    evidence = alert.get("evidence", {})
    if evidence:
        st.markdown("**Evidence summary**")
        evidence_cols = st.columns(4)
        evidence_cols[0].metric(
            "Repeated amount",
            f"{evidence.get('repeated_amount', 0):,.2f}",
        )
        evidence_cols[1].metric(
            "Repeat count",
            evidence.get("repeat_count", 0),
        )
        evidence_cols[2].metric(
            "Velocity ratio",
            evidence.get("velocity_ratio", 0),
        )
        evidence_cols[3].metric(
            "Runway hours",
            evidence.get("runway_hours", 0),
        )

    st.success(f"Recommended next step: {alert['recommended_next_step']}")
    st.caption(f"Owner: {alert['owner']} · Created: {alert['created_at']}")


def render_uncertainty_callout(freshness: str, uncertainty: str) -> None:
    """Show uncertainty when data freshness is reduced."""

    if freshness in {"delayed", "stale"}:
        render_freshness_badge(freshness)
        st.warning(
            f"Forecast confidence is reduced. {uncertainty} "
            "Treat recommendations as provisional until the feed recovers."
        )
