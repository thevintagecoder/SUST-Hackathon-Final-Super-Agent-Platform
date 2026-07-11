"""Ops Center dashboard — demo story entry point."""

from __future__ import annotations

from html import escape

import streamlit as st

from frontend.api.client import BackendClient
from frontend.components.common import (
    DEMO_MAIN_AGENT,
    SAMPLE_SCENARIO_ID,
    agent_display_name,
    cached_list_alerts,
    cached_management_dashboard,
    cached_operations_dashboard,
    cached_provider_dashboard,
    money,
    numeric_sum,
    provider_label,
    run_api_call,
    safety_notice,
)


def _agent_investigate_status(
    *,
    agent_code: str,
    row: dict,
) -> tuple[str, str, bool]:
    """Return display code, status line, and whether row is alert."""

    alerts = int(row.get("active_alert_count") or 0)
    stale = int(row.get("stale_provider_count") or 0)
    severity = str(
        row.get("highest_active_severity") or ""
    ).upper()

    if agent_code == DEMO_MAIN_AGENT and (
        alerts > 0
        or stale > 0
        or severity in {"HIGH", "CRITICAL", "MEDIUM"}
    ):
        return (
            agent_code,
            "⚠ Liquidity warning & unusual activity",
            True,
        )

    if alerts > 0 or severity in {"HIGH", "CRITICAL"}:
        return (
            agent_code,
            f"⚠ {alerts} active alert(s) — review needed",
            True,
        )

    if stale > 0:
        return (
            agent_code,
            "⚠ Delayed provider feed — verify balance",
            True,
        )

    return (agent_code, "Normal status", False)


def _load_overview_data(
    client: BackendClient,
) -> tuple[dict | None, dict | None, list[dict], dict | None]:
    """Load dashboard aggregates."""

    scenario_id = st.session_state.get(
        "scenario_id",
        SAMPLE_SCENARIO_ID,
    )
    base_url = client.base_url

    operations = run_api_call(
        "Loading Ops Center…",
        lambda: cached_operations_dashboard(
            base_url,
            scenario_id,
            12,
        ),
    )
    management = run_api_call(
        "Loading portfolio totals…",
        lambda: cached_management_dashboard(
            base_url,
            scenario_id,
        ),
    )

    providers: list[dict] = []
    for provider_code in ("NAGAD_SIM", "BKASH_SIM"):
        result = run_api_call(
            f"Loading {provider_label(provider_code)}…",
            lambda code=provider_code: cached_provider_dashboard(
                base_url,
                code,
                scenario_id,
                5,
            ),
        )
        if result is not None:
            providers.append(result)

    alerts = run_api_call(
        "Loading alerts…",
        lambda: cached_list_alerts(
            base_url,
            scenario_id,
            12,
        ),
    )

    return operations, management, providers, alerts


def _render_hero(
    *,
    active_agents: int,
    total_agents: int,
    active_alerts: int,
    high_alerts: int,
) -> None:
    """Render the blue Ops Center header."""

    new_badge = (
        f'<span class="ops-badge-new">{high_alerts} New</span>'
        if high_alerts > 0
        else ""
    )
    alert_line = (
        '<div class="ops-hero-metric-delta alert">'
        "▲ HIGH priority</div>"
        if high_alerts > 0
        else '<div class="ops-hero-metric-delta">Stable</div>'
    )

    st.markdown(
        f"""
        <div class="ops-hero">
            <div class="ops-hero-title">Ops Center</div>
            <div class="ops-hero-sub">
                Sylhet agent network · synthetic demonstration only
            </div>
            <div class="ops-hero-metrics">
                <div class="ops-hero-metric">
                    <div class="ops-hero-metric-label">Active Agents</div>
                    <div class="ops-hero-metric-value">{active_agents:,}</div>
                    <div class="ops-hero-metric-delta up">
                        of {total_agents:,} total
                    </div>
                </div>
                <div class="ops-hero-metric">
                    {new_badge}
                    <div class="ops-hero-metric-label">Active Alerts</div>
                    <div class="ops-hero-metric-value">{active_alerts}</div>
                    {alert_line}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_provider_health(providers: list[dict]) -> None:
    """Render Nagad / bKash feed health cards."""

    st.markdown(
        '<div class="section-heading">Provider Health</div>',
        unsafe_allow_html=True,
    )

    rows_html = ""
    for item in providers:
        identity = item.get("provider", {})
        summary = item.get("summary", {})
        code = identity.get("code", "")
        fresh = int(summary.get("fresh_balance_count") or 0)
        stale = int(summary.get("non_fresh_balance_count") or 0)
        total = int(summary.get("agents_with_balance_count") or 0)

        if code == "NAGAD_SIM":
            icon_class = "nagad"
            icon_char = "⚡"
            name = "Nagad API"
        else:
            icon_class = "bkash"
            icon_char = "💳"
            name = "bKash API"

        if stale > 0:
            uptime = "Verify feed"
            badge_class = "uptime-badge warn"
            latency = f"{stale} delayed balance(s)"
        else:
            uptime = "99.9% Uptime" if stale == 0 and fresh > 0 else "Live"
            badge_class = "uptime-badge"
            latency = f"{fresh}/{total} agents fresh"

        rows_html += f"""
        <div class="provider-row">
            <div class="provider-row-left">
                <div class="provider-icon {icon_class}">{icon_char}</div>
                <div>
                    <div class="provider-name">{escape(name)}</div>
                    <div class="provider-meta">Feed status: {escape(latency)}</div>
                </div>
            </div>
            <span class="{badge_class}">{escape(uptime)}</span>
        </div>
        """

    st.markdown(
        f'<div class="ops-card">{rows_html}</div>',
        unsafe_allow_html=True,
    )


def _render_secondary_metrics(
    *,
    shared_cash: str,
    open_cases: int,
) -> None:
    """Shared cash and open cases mini-cards."""

    st.markdown(
        f"""
        <div class="ops-card-grid">
            <div class="ops-mini-card">
                <div class="ops-mini-icon cash">💵</div>
                <div class="ops-mini-label">Shared Cash</div>
                <div class="ops-mini-value">{escape(shared_cash)}</div>
            </div>
            <div class="ops-mini-card">
                <div class="ops-mini-icon cases">📋</div>
                <div class="ops-mini-label">Open Cases</div>
                <div class="ops-mini-value">{open_cases} Active</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_investigate(
    agent_rows: list[dict],
) -> None:
    """Agent list with SYL-001 highlighted for the demo story."""

    st.markdown(
        '<div class="section-heading">Investigate</div>',
        unsafe_allow_html=True,
    )

    if not agent_rows:
        st.info(
            "Load **NETWORK-001** into PostgreSQL, then refresh. "
            "See README for the loader command."
        )
        return

    sorted_rows = sorted(
        agent_rows,
        key=lambda row: (
            0 if row.get("agent_code") == DEMO_MAIN_AGENT else 1,
            row.get("agent_code", ""),
        ),
    )

    for row in sorted_rows[:6]:
        code = str(row.get("agent_code") or "")
        display_code, status, is_alert = (
            _agent_investigate_status(
                agent_code=code,
                row=row,
            )
        )
        avatar_class = "agent-avatar alert" if is_alert else "agent-avatar"
        status_class = (
            "investigate-status alert"
            if is_alert
            else "investigate-status ok"
        )
        label = agent_display_name(code)

        col_card, col_btn = st.columns([5, 1])
        with col_card:
            st.markdown(
                f"""
                <div class="ops-card" style="margin-bottom:0.5rem;padding:0.75rem 1rem">
                    <div class="investigate-row" style="border:none;padding:0">
                        <div class="investigate-left">
                            <div class="{avatar_class}">👤</div>
                            <div>
                                <div class="investigate-code">{escape(display_code)}</div>
                                <div style="font-size:0.78rem;color:#64748b">{escape(label)}</div>
                                <div class="{status_class}">{escape(status)}</div>
                            </div>
                        </div>
                        <span class="investigate-chevron">›</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button(
                "Open",
                key=f"investigate_{code}",
                type="primary" if code == DEMO_MAIN_AGENT else "secondary",
            ):
                st.session_state["current_page"] = "Liquidity"
                st.session_state["scenario_id"] = "NETWORK-001"
                for label_key, sid in st.session_state.get(
                    "_scenario_options", {}
                ).items():
                    if sid == "NETWORK-001":
                        st.session_state["scenario_label"] = label_key
                        break
                st.session_state["svc_agent"] = code
                st.session_state["svc_provider"] = "NAGAD_SIM"
                st.session_state["svc_tx_type"] = "cash_in"
                st.session_state["svc_amount"] = 80000.0
                st.rerun()


def render_overview(client: BackendClient) -> None:
    """Render the Ops Center dashboard."""

    operations, management, providers, alert_data = (
        _load_overview_data(client)
    )
    if operations is None or management is None:
        return

    safety_notice(operations.get("synthetic_data_notice"))

    summary = operations.get("summary", {})
    agent_rows = operations.get("agent_risks", [])
    shared_cash_total = money(
        numeric_sum(
            [row.get("shared_cash") for row in agent_rows]
        )
    )

    active_alerts = int(summary.get("active_alert_count") or 0)
    high_alerts = int(
        summary.get("high_or_critical_alert_count") or 0
    )
    open_cases = int(
        summary.get("unassigned_alert_count") or 0
    ) + int(management.get("summary", {}).get(
        "open_support_request_count", 0
    ) or 0)

    _render_hero(
        active_agents=int(summary.get("active_agents") or 0),
        total_agents=int(summary.get("total_agents") or 0),
        active_alerts=active_alerts,
        high_alerts=high_alerts,
    )

    _render_provider_health(providers)
    _render_secondary_metrics(
        shared_cash=shared_cash_total,
        open_cases=open_cases,
    )
    _render_investigate(agent_rows)

    st.markdown(
        '<div class="section-heading">Demo path</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="notice">'
        "<b>Start with Zindabazar (AGENT-SYL-001).</b> "
        "Use <b>Liquidity</b> for the ৳80k Nagad cash-in check, network "
        "support, and runway forecast. Use <b>Anomalies</b> for repeated "
        "bKash patterns. Use <b>Cases</b> to accept → escalate → resolve."
        "</div>",
        unsafe_allow_html=True,
    )

    alerts = (alert_data or {}).get("items", [])
    active = [
        a for a in alerts if a.get("status") != "RESOLVED"
    ]
    if active:
        st.caption(
            f"{len(active)} alert(s) waiting — open the "
            "**Cases** tab to review."
        )
