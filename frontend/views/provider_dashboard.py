"""Provider network view for bKash, Nagad, and Rocket."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend.api.client import BackendClient
from frontend.components.common import (
    KNOWN_PROVIDER_CODES,
    format_timestamp,
    money,
    metric_row,
    provider_label,
    render_alert_card,
    render_empty_state,
    run_api_call,
    safety_notice,
)


def render_provider_dashboard(client: BackendClient) -> None:
    """Render one provider intelligence dashboard."""

    st.header("Provider network")
    st.markdown(
        '<div class="section-intro">'
        "Track provider electronic float separately from shared "
        "Agent cash. Use this when bKash or Nagad needs to know "
        "which Agents are at threshold, stale, or under review."
        "</div>",
        unsafe_allow_html=True,
    )
    safety_notice()

    provider_code = st.radio(
        "Provider",
        KNOWN_PROVIDER_CODES,
        index=KNOWN_PROVIDER_CODES.index("NAGAD_SIM"),
        format_func=provider_label,
        horizontal=True,
    )
    scenario_id = st.session_state.get("scenario_id")

    data = run_api_call(
        "Loading Provider dashboard…",
        lambda: client.provider_dashboard(
            provider_code,
            scenario_id=scenario_id,
            recent_alert_limit=10,
        ),
    )

    if data is None:
        return

    if data.get("synthetic_data_notice"):
        st.info(data["synthetic_data_notice"])

    provider = data.get("provider", {})
    summary = data.get("summary", {})

    st.subheader(
        f"{provider_label(provider.get('code', provider_code))} "
        "field network"
    )

    metric_row(
        [
            (
                "Agents with balance",
                summary.get("agents_with_balance"),
            ),
            (
                "Total electronic float",
                money(summary.get("total_electronic_balance")),
            ),
            (
                "Safety threshold",
                money(summary.get("prototype_safety_threshold")),
            ),
            (
                "At/below safety",
                summary.get("at_or_below_safety_threshold_count"),
            ),
            ("Fresh feeds", summary.get("fresh_balance_count")),
            (
                "Non-fresh feeds",
                summary.get("non_fresh_balance_count"),
            ),
            (
                "High/Critical",
                summary.get("high_or_critical_alert_count"),
            ),
        ]
    )

    st.subheader("Agent balances")
    balances = data.get("agent_balances", [])
    if balances:
        balance_frame = pd.DataFrame(balances)
        severity_order = {
            "CRITICAL": 0,
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3,
        }
        balance_frame["risk_sort"] = (
            balance_frame["highest_active_severity"]
            .map(severity_order)
            .fillna(4)
        )
        balance_frame = balance_frame.sort_values(
            [
                "risk_sort",
                "at_or_below_safety_threshold",
                "freshness_state",
                "agent_code",
            ],
            ascending=[True, False, True, True],
        )
        display = balance_frame[
            [
                "agent_code",
                "agent_name",
                "electronic_balance",
                "prototype_safety_threshold",
                "at_or_below_safety_threshold",
                "freshness_state",
                "last_update_at",
                "active_alert_count",
                "highest_active_severity",
            ]
        ].copy()
        display["last_update_at"] = display["last_update_at"].map(
            format_timestamp
        )
        st.dataframe(
            display,
            width="stretch",
            hide_index=True,
            column_config={
                "agent_code": "Agent",
                "agent_name": "Name",
                "electronic_balance": st.column_config.NumberColumn(
                    "Electronic float",
                    format="৳ %.2f",
                ),
                "prototype_safety_threshold": (
                    st.column_config.NumberColumn(
                        "Safety threshold",
                        format="৳ %.2f",
                    )
                ),
                "at_or_below_safety_threshold": "At/below threshold",
                "freshness_state": "Feed state",
                "last_update_at": "Last update",
                "active_alert_count": "Alerts",
                "highest_active_severity": "Highest risk",
            },
        )
    else:
        render_empty_state(
            "No provider balances",
            "Load the synthetic data for this provider, then refresh.",
        )

    st.subheader("Recent alerts")
    recent_alerts = [
        alert
        for alert in data.get("recent_alerts", [])
        if alert.get("status") != "RESOLVED"
    ]
    if not recent_alerts:
        render_empty_state(
            "No risk alerts yet",
            "Resolved alerts are hidden here. Run a customer check or "
            "risk check to create one.",
        )
    else:
        for alert in recent_alerts:
            render_alert_card(alert)
