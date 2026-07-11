"""Anomaly Alerts: unusual-activity flags with expandable evidence."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from core.anomaly import detect_anomalies
from core.data_access import DataUnavailableError
from frontend.components.filters import get_repository, render_sidebar_filters

SEVERITY_COLORS = {"high": "red", "medium": "orange", "low": "gray"}

st.title("Anomaly Alerts")
st.caption(
    "Unusual-activity flags for human review. A flag is evidence to "
    "examine — it is never a determination of fraud."
)

filters = render_sidebar_filters(include_providers=True)
if filters is None:
    st.stop()

repository = get_repository()

try:
    all_flags = detect_anomalies(
        repository,
        filters.scenario.scenario_id,
        filters.agent_code,
    )
except DataUnavailableError as exc:
    st.error(str(exc))
    st.stop()

flags = [
    flag
    for flag in all_flags
    if flag.provider_code in filters.provider_codes
]

if not flags:
    st.success(
        f"No unusual activity flagged for agent {filters.agent_code} in "
        f"scenario '{filters.scenario.name}' with the current provider "
        "filter."
    )
    st.stop()

st.metric("Open flags", len(flags))

for flag in flags:
    with st.expander(
        f"{flag.severity.upper()} · {flag.title}",
        expanded=flag.severity == "high",
    ):
        badge_cols = st.columns([1, 1, 2])
        with badge_cols[0]:
            st.badge(
                f"Severity: {flag.severity}",
                color=SEVERITY_COLORS.get(flag.severity, "gray"),
            )
        with badge_cols[1]:
            st.badge(f"Confidence: {flag.confidence * 100:.0f}%", color="blue")
        with badge_cols[2]:
            st.badge(flag.provider_code, color="gray")

        st.write(flag.reason)
        st.warning(flag.uncertainty)

        if flag.metrics:
            metric_cols = st.columns(len(flag.metrics))
            for column, (key, value) in zip(
                metric_cols,
                flag.metrics.items(),
                strict=True,
            ):
                column.metric(key.replace("_", " ").title(), value)

        st.markdown("**Evidence — the flagged transactions**")
        evidence_view = flag.evidence[
            [
                "external_id",
                "occurred_at",
                "provider_code",
                "transaction_type",
                "amount",
                "synthetic_customer_id",
            ]
        ].rename(
            columns={
                "external_id": "Transaction",
                "occurred_at": "Occurred at",
                "provider_code": "Provider",
                "transaction_type": "Type",
                "amount": "Amount",
                "synthetic_customer_id": "Customer (synthetic)",
            }
        )
        st.dataframe(evidence_view, hide_index=True, use_container_width=True)

        st.success(f"Recommended next step: {flag.recommended_next_step}")
        st.caption(
            "Track the review outcome on the Admin Case Management page."
        )
