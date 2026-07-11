"""Field-Agent workspace for customer liquidity service."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend.api.client import BackendClient
from frontend.components.common import (
    KNOWN_AGENT_CODES,
    SAMPLE_AGENT_CODE,
    SAMPLE_SCENARIO_ID,
    agent_display_name,
    format_timestamp,
    freshness_label,
    provider_css_class,
    provider_label,
    render_alert_card,
    render_balance_card,
    render_empty_state,
    run_api_call,
    safety_notice,
    severity_label,
)


def render_agent_dashboard(client: BackendClient) -> None:
    """Render a practical Agent-facing liquidity workspace."""

    st.header("Agent desk")
    st.markdown(
        '<div class="section-intro">'
        "You are the field agent. Check what you can serve before "
        "accepting a customer request. Physical cash is shared; "
        "electronic float is provider-specific."
        "</div>",
        unsafe_allow_html=True,
    )
    safety_notice()

    scenario_id = st.session_state.get("scenario_id")
    current = st.session_state.get(
        "selected_agent",
        SAMPLE_AGENT_CODE,
    )
    if current not in KNOWN_AGENT_CODES:
        current = SAMPLE_AGENT_CODE

    agent_code = st.selectbox(
        "Working as",
        KNOWN_AGENT_CODES,
        index=KNOWN_AGENT_CODES.index(current),
        format_func=agent_display_name,
    )
    st.session_state["selected_agent"] = agent_code

    data = run_api_call(
        "Loading Agent position…",
        lambda: client.agent_dashboard(
            agent_code,
            scenario_id=scenario_id,
            recent_alert_limit=10,
        ),
    )

    if data is None:
        return

    agent = data.get("agent", {})
    shared_cash = data.get("shared_cash", {})
    risk = data.get("risk_summary", {})

    heading, status = st.columns([4, 1])
    heading.subheader(agent.get("name", agent_display_name(agent_code)))
    if agent.get("is_active"):
        status.success("Active agent")
    else:
        status.error("Inactive agent")
    st.caption(
        f"{agent.get('area', 'Unknown area')} · "
        f"{agent.get('code', agent_code)}"
    )

    st.markdown("### Available liquidity")
    balances = data.get("provider_balances", [])
    cards = st.columns(1 + max(len(balances), 1))
    with cards[0]:
        render_balance_card(
            title="Shared physical cash",
            amount=shared_cash.get("balance")
            if shared_cash.get("available")
            else None,
            eyebrow="For customer cash-out",
            meta=(
                "Shared across bKash, Nagad and other providers · "
                f"{format_timestamp(shared_cash.get('as_of'))}"
            ),
            css_class="cash",
        )

    for column, balance in zip(cards[1:], balances):
        with column:
            provider_code = balance.get("provider_code")
            render_balance_card(
                title=f"{provider_label(provider_code)} float",
                amount=balance.get("electronic_balance"),
                eyebrow="For customer cash-in",
                meta=(
                    f"{freshness_label(balance.get('freshness_state'))}"
                    " · "
                    f"{format_timestamp(balance.get('last_update_at'))}"
                ),
                css_class=provider_css_class(provider_code),
            )

    if not balances:
        with cards[-1]:
            render_empty_state(
                "No provider balances",
                "Provider float has not been loaded for this Agent.",
            )

    _render_liquidity_chart(
        shared_cash=shared_cash,
        balances=balances,
    )

    risk_columns = st.columns(3)
    risk_columns[0].metric(
        "Open alerts",
        risk.get("active_alert_count", 0),
    )
    risk_columns[1].metric(
        "Highest risk",
        severity_label(risk.get("highest_active_severity"))
        if risk.get("highest_active_severity")
        else "Clear",
    )
    risk_columns[2].metric(
        "Human review",
        "Required"
        if risk.get("human_review_required")
        else "Not currently",
    )
    risk_columns[0].caption(
        "Resolved alerts are removed from active risk."
    )
    risk_columns[1].caption(
        severity_label(risk.get("highest_active_severity"))
        if risk.get("highest_active_severity")
        else "No active risk for the selected alert scenario."
    )
    risk_columns[2].caption(
        "Automatic action: "
        + (
            "reported"
            if risk.get("automatic_action_taken")
            else "none"
        )
    )

    _render_attention_section(data, agent_code)


def _render_liquidity_chart(
    *,
    shared_cash: dict,
    balances: list[dict],
) -> None:
    """Bar chart of the agent's liquidity by resource."""

    rows = []
    if shared_cash.get("available"):
        try:
            rows.append(
                {
                    "Resource": "Shared cash",
                    "Balance (৳)": float(shared_cash.get("balance") or 0),
                }
            )
        except (TypeError, ValueError):
            pass
    for balance in balances:
        try:
            rows.append(
                {
                    "Resource": f"{provider_label(balance.get('provider_code'))} float",
                    "Balance (৳)": float(
                        balance.get("electronic_balance") or 0
                    ),
                }
            )
        except (TypeError, ValueError):
            continue

    if len(rows) < 2:
        return

    st.markdown("**Liquidity at a glance**")
    st.bar_chart(
        pd.DataFrame(rows),
        x="Resource",
        y="Balance (৳)",
        height=240,
    )


def _render_attention_section(data: dict, agent_code: str) -> None:
    st.markdown("### What needs attention")
    recent_alerts = [
        alert
        for alert in data.get("recent_alerts", [])
        if alert.get("status") != "RESOLVED"
    ]
    if not recent_alerts:
        render_empty_state(
            "No risk alerts yet",
            "Before serving a large customer request, run a check on "
            "Customer service. If cash is short, prompt an alert.",
        )
    else:
        for alert in recent_alerts:
            render_alert_card(
                alert,
                context_agent_code=agent_code,
            )
