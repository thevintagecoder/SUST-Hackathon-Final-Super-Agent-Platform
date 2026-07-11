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
    cached_management_dashboard,
    cached_provider_dashboard,
    format_timestamp,
    freshness_label,
    money,
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
    nav_cols = st.columns([3, 1])
    with nav_cols[1]:
        if st.button(
            "Network overview",
            key="agent_network_overview",
            type="secondary",
            use_container_width=True,
        ):
            st.session_state["current_page"] = "Network"
            st.rerun()
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
    _render_bottleneck_callout(
        client=client,
        agent_code=agent_code,
        balances=balances,
        scenario_id=scenario_id,
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


def _render_bottleneck_callout(
    *,
    client: BackendClient,
    agent_code: str,
    balances: list[dict],
    scenario_id: str | None,
) -> None:
    """Highlight the provider most likely to block customer service."""

    if len(balances) < 2:
        return

    management = cached_management_dashboard(
        client.base_url,
        scenario_id,
    )
    risk_by_provider = {
        str(row.get("provider_code") or ""): row
        for row in management.get("provider_risks", [])
    }

    comparisons: list[dict] = []
    for balance in balances:
        provider_code = str(balance.get("provider_code") or "")
        try:
            agent_balance = float(balance.get("electronic_balance") or 0)
        except (TypeError, ValueError):
            continue
        risk = risk_by_provider.get(provider_code, {})
        agents_with_balance = int(risk.get("agents_with_balance") or 1) or 1
        try:
            network_total = float(
                risk.get("total_electronic_balance") or 0
            )
        except (TypeError, ValueError):
            network_total = 0.0
        network_avg = network_total / agents_with_balance
        ratio = (
            agent_balance / network_avg
            if network_avg > 0
            else 1.0
        )
        comparisons.append(
            {
                "provider_code": provider_code,
                "agent_balance": agent_balance,
                "network_avg": network_avg,
                "ratio": ratio,
            }
        )

    if not comparisons:
        return

    bottleneck = min(comparisons, key=lambda row: row["ratio"])
    others_healthy = any(
        row["ratio"] >= 0.8
        and row["provider_code"] != bottleneck["provider_code"]
        for row in comparisons
    )

    provider_data = cached_provider_dashboard(
        client.base_url,
        bottleneck["provider_code"],
        scenario_id,
        5,
    )
    agent_row = next(
        (
            row
            for row in provider_data.get("agent_balances", [])
            if row.get("agent_code") == agent_code
        ),
        None,
    )
    at_threshold = bool(
        agent_row and agent_row.get("at_or_below_safety_threshold")
    )

    if not at_threshold and not (
        bottleneck["ratio"] < 0.6 and others_healthy
    ):
        return

    provider_name = provider_label(bottleneck["provider_code"])
    if at_threshold and others_healthy:
        detail = (
            f"{provider_name} is at or below the safety threshold "
            f"({money(agent_row.get('prototype_safety_threshold'))}) "
            "while your other provider floats look healthier."
        )
    else:
        detail = (
            f"{provider_name} is your bottleneck — "
            f"{money(bottleneck['agent_balance'])} on hand vs "
            f"{money(bottleneck['network_avg'])} network average "
            "per agent."
        )

    st.warning(
        f"**Bottleneck provider:** {detail} "
        "Use **Liquidity → Find support** before large cash-ins on "
        f"{provider_name}."
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
