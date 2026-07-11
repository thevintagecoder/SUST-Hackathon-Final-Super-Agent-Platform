"""Operations stakeholder dashboard view."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend.api.client import BackendClient
from frontend.components.common import (
    money,
    metric_row,
    render_alert_card,
    render_empty_state,
    run_api_call,
    safety_notice,
)


def render_operations_dashboard(client: BackendClient) -> None:
    """Render the Operations intelligence dashboard."""

    st.header("Operations control room")
    st.markdown(
        '<div class="section-intro">'
        "Triage non-fresh provider feeds, high/critical alerts, "
        "and unassigned human-review work across all Agents."
        "</div>",
        unsafe_allow_html=True,
    )
    safety_notice()

    scenario_id = st.session_state.get("scenario_id")
    recent_alert_limit = st.slider(
        "Recent alerts to review",
        min_value=5,
        max_value=50,
        value=10,
        step=5,
    )

    data = run_api_call(
        "Loading Operations dashboard…",
        lambda: client.operations_dashboard(
            scenario_id=scenario_id,
            recent_alert_limit=int(recent_alert_limit),
        ),
    )

    if data is None:
        return

    if data.get("synthetic_data_notice"):
        st.info(data["synthetic_data_notice"])

    summary = data.get("summary", {})
    metric_row(
        [
            ("Total Agents", summary.get("total_agents")),
            ("Active Agents", summary.get("active_agents")),
            ("Active alerts", summary.get("active_alert_count")),
            ("Escalated", summary.get("escalated_alert_count")),
            ("Unassigned", summary.get("unassigned_alert_count")),
            (
                "High/Critical",
                summary.get("high_or_critical_alert_count"),
            ),
            (
                "Human review",
                summary.get("human_review_required_count"),
            ),
            (
                "Non-fresh feeds",
                summary.get("stale_provider_balance_count"),
            ),
        ]
    )

    st.subheader("Agent risk table")
    risks = data.get("agent_risks", [])
    if risks:
        risk_frame = pd.DataFrame(risks)
        severity_order = {
            "CRITICAL": 0,
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3,
        }
        risk_frame["risk_sort"] = (
            risk_frame["highest_active_severity"]
            .map(severity_order)
            .fillna(4)
        )
        risk_frame = risk_frame.sort_values(
            [
                "risk_sort",
                "active_alert_count",
                "stale_provider_count",
                "agent_code",
            ],
            ascending=[True, False, False, True],
        )
        display = risk_frame[
            [
                "agent_code",
                "agent_name",
                "area",
                "shared_cash",
                "stale_provider_count",
                "active_alert_count",
                "highest_active_severity",
                "human_review_required",
            ]
        ].copy()
        display["shared_cash"] = pd.to_numeric(
            display["shared_cash"],
            errors="coerce",
        )
        st.dataframe(
            display,
            width="stretch",
            hide_index=True,
            column_config={
                "agent_code": "Agent",
                "agent_name": "Name",
                "area": "Area",
                "shared_cash": st.column_config.NumberColumn(
                    "Shared cash",
                    format="৳ %.2f",
                ),
                "stale_provider_count": "Non-fresh feeds",
                "active_alert_count": "Active alerts",
                "highest_active_severity": "Highest severity",
                "human_review_required": "Human review",
            },
        )
    else:
        render_empty_state(
            "No Agent rows",
            "Load synthetic Agent balances, then refresh.",
        )

    st.subheader("Active review queue")
    alerts = [
        alert
        for alert in data.get("recent_alerts", [])
        if alert.get("status") != "RESOLVED"
    ]
    if not alerts:
        render_empty_state(
            "No risk alerts yet",
            "Run a customer check or risk check to create one when "
            "evidence supports it.",
        )
    else:
        for alert in alerts:
            render_alert_card(alert)

    st.caption(
        "Shared cash total in view: "
        + money(
            pd.to_numeric(
                pd.Series(
                    [row.get("shared_cash") for row in risks],
                    dtype="object",
                ),
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )
    )
