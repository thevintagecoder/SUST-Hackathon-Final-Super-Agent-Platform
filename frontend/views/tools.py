"""Customer service tools: serviceability, network, forecast, anomaly."""

from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from frontend.api.client import BackendClient
from frontend.components.common import (
    ANOMALY_RECIPES,
    FORECAST_RECIPES,
    KNOWN_AGENT_CODES,
    KNOWN_PROVIDER_CODES,
    NETWORK_RECIPES,
    RESOURCE_TYPES,
    SAMPLE_AGENT_CODE,
    SAMPLE_SCENARIO_ID,
    SERVICEABILITY_RECIPES,
    TRANSACTION_TYPES,
    DemoRecipe,
    agent_display_name,
    cached_evaluation_dashboard,
    freshness_label,
    money,
    optional_text,
    provider_label,
    render_recipe_cards,
    render_scenario_context,
    render_technical_detail,
    run_api_call,
    safety_notice,
)
from frontend.components.scenarios import SCENARIO_REGISTRY


def render_tools(client: BackendClient) -> None:
    """Legacy entry — liquidity + anomalies combined."""

    render_liquidity(client)


def render_liquidity(client: BackendClient) -> None:
    """Liquidity checks: serviceability, network support, runway."""

    st.header("Liquidity")
    st.markdown(
        '<div class="section-intro">'
        "Step through the Zindabazar shortfall story — check whether "
        "the agent can serve a customer, find nearby float, then estimate "
        "runway before the safety threshold."
        "</div>",
        unsafe_allow_html=True,
    )
    safety_notice()
    render_scenario_context()

    liquidity_tabs = [
        ("service", "Can we serve?"),
        ("network", "Find support"),
        ("forecast", "Runway forecast"),
    ]
    tab_keys = [key for key, _ in liquidity_tabs]
    tab_labels = [label for _, label in liquidity_tabs]
    active_tab = st.session_state.get("liquidity_tab", "service")
    if active_tab not in tab_keys:
        active_tab = "service"
    selected_label = st.radio(
        "Liquidity section",
        tab_labels,
        index=tab_keys.index(active_tab),
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state["liquidity_tab"] = tab_keys[
        tab_labels.index(selected_label)
    ]

    if st.session_state["liquidity_tab"] == "service":
        _render_serviceability(client)
    elif st.session_state["liquidity_tab"] == "network":
        _render_network(client)
    else:
        _render_forecast(client)


def render_anomalies(client: BackendClient) -> None:
    """Unusual activity detection for the demo story."""

    st.header("Anomalies")
    st.markdown(
        '<div class="section-intro">'
        "Detect repeated bKash amounts and velocity spikes. "
        "The system flags patterns for human review — it never "
        "declares fraud on its own."
        "</div>",
        unsafe_allow_html=True,
    )
    safety_notice()
    _render_anomaly_quality_disclosure(client)
    render_scenario_context()
    _render_anomaly(client)


def _render_anomaly_quality_disclosure(client: BackendClient) -> None:
    """Show controlled benchmark false-positive metrics on the main demo path."""

    data = cached_evaluation_dashboard(client.base_url)
    if not data:
        return

    anomaly = data.get("anomaly", {})
    checks = data.get("responsible_ai_checks", {})
    scenarios = anomaly.get("evaluated_scenarios") or []

    st.markdown("#### Prototype quality (controlled synthetic benchmark)")
    st.caption(
        "Rule-based flags mean review — not confirmed fraud. "
        "Metrics below come from GET /dashboards/evaluation."
    )

    cols = st.columns(4)
    cols[0].metric("False positives", anomaly.get("false_positive", 0))
    cols[1].metric(
        "False positive rate",
        anomaly.get("false_positive_rate", "—"),
    )
    cols[2].metric("Precision", anomaly.get("precision", "—"))
    cols[3].metric("Recall", anomaly.get("recall", "—"))

    scenario_line = (
        f" Scenarios: {', '.join(scenarios)}."
        if scenarios
        else ""
    )
    if checks.get("anomaly_declared_as_confirmed_fraud") is False:
        st.info(
            "This prototype never auto-labels fraud. "
            f"On the synthetic benchmark, false positive rate is "
            f"{anomaly.get('false_positive_rate', '—')}"
            f" ({anomaly.get('false_positive', 0)} false alarm(s) on "
            f"NORMAL-001 vs {anomaly.get('true_positive', 0)} intended "
            f"flag on REPEATED-001).{scenario_line} Human review is still "
            "required for every flag."
        )


# ── Serviceability ────────────────────────────────────────────────────────────

def _render_serviceability(client: BackendClient) -> None:
    st.markdown(
        "**Can the agent serve this customer right now?**  \n"
        "Cash-out uses shared physical cash. Cash-in uses provider float."
    )

    clicked = render_recipe_cards(SERVICEABILITY_RECIPES, key_prefix="svc")
    if clicked:
        _apply_recipe(clicked, prefix="svc")
        st.rerun()

    st.divider()

    default_idx_agent = KNOWN_AGENT_CODES.index(
        st.session_state.get("svc_agent", SAMPLE_AGENT_CODE)
    ) if st.session_state.get("svc_agent") in KNOWN_AGENT_CODES else 0

    default_idx_provider = KNOWN_PROVIDER_CODES.index(
        st.session_state.get("svc_provider", "BKASH_SIM")
    ) if st.session_state.get("svc_provider") in KNOWN_PROVIDER_CODES else 0

    default_tx_idx = TRANSACTION_TYPES.index(
        st.session_state.get("svc_tx_type", "cash_in")
    ) if st.session_state.get("svc_tx_type") in TRANSACTION_TYPES else 0

    default_amount = float(
        st.session_state.get("svc_amount", 50000.0)
    )

    with st.form("serviceability_form"):
        col_a, col_b = st.columns(2)
        agent_code = col_a.selectbox(
            "Agent (branch)",
            KNOWN_AGENT_CODES,
            index=default_idx_agent,
            format_func=agent_display_name,
        )
        provider_code = col_b.selectbox(
            "Customer's provider",
            KNOWN_PROVIDER_CODES,
            index=default_idx_provider,
            format_func=provider_label,
        )
        col_c, col_d = st.columns(2)
        transaction_type = col_c.selectbox(
            "Customer wants to",
            TRANSACTION_TYPES,
            index=default_tx_idx,
            format_func=lambda v: (
                "Cash-in  (customer deposits, agent sends e-money)"
                if v == "cash_in"
                else "Cash-out (customer withdraws physical cash)"
            ),
        )
        amount = col_d.number_input(
            "Amount (৳)",
            min_value=1.0,
            value=default_amount,
            step=1000.0,
        )
        submitted = st.form_submit_button(
            "Check before serving",
            type="primary",
        )

    if submitted:
        result = run_api_call(
            "Checking current balances…",
            lambda: client.check_serviceability(
                {
                    "agent_code": agent_code,
                    "provider_code": provider_code,
                    "transaction_type": transaction_type,
                    "amount": amount,
                }
            ),
        )
        if result is not None:
            st.session_state["serviceability_result"] = result

    result = st.session_state.get("serviceability_result")
    if result is None:
        st.caption(
            "Pick a scenario card above or fill in the form, "
            "then click **Check before serving**."
        )
        return

    _render_serviceability_result(result, client)


def _render_serviceability_result(
    result: dict,
    client: BackendClient,
) -> None:
    """Show serviceability result in human-readable format."""

    serviceable = result.get("serviceable", False)
    available = result.get("available_amount", 0)
    shortfall = result.get("shortfall", 0)
    tx_type = result.get("transaction_type", "")
    provider = provider_label(result.get("provider_code"))
    req_amount = result.get("requested_amount", 0)

    resource = (
        f"{provider} electronic float"
        if tx_type == "cash_in"
        else "shared physical cash"
    )

    if serviceable:
        st.markdown(
            f'<div class="result-banner pass">'
            f"✓ CAN SERVE — {money(req_amount)} {tx_type.replace('_', '-')}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"**{money(available)}** available in {resource}. "
            "You can accept this customer request."
        )
    else:
        st.markdown(
            f'<div class="result-banner fail">'
            f"✗ CANNOT SERVE — short by {money(shortfall)}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"**{money(available)}** available in {resource}, "
            f"but customer needs **{money(req_amount)}**. "
            f"Short by **{money(shortfall)}**."
        )

    exp = result.get("explanation", "")
    if exp:
        st.write(exp)

    actions = result.get("recommended_actions", [])
    if actions:
        st.markdown("**What to do next:**")
        for action in actions:
            st.write(f"- {action}")

    if (
        not serviceable
        and st.button(
            "Prompt shortfall alert for operations",
            type="primary",
            key="prompt_alert_btn",
        )
    ):
        alert_result = run_api_call(
            "Creating evidence-backed alert…",
            lambda: client.generate_alert(
                {
                    "alert_type": "SERVICEABILITY_SHORTFALL",
                    "agent_code": result["agent_code"],
                    "provider_code": result["provider_code"],
                    "scenario_id": st.session_state.get(
                        "scenario_id", SAMPLE_SCENARIO_ID
                    ),
                    "transaction_type": result["transaction_type"],
                    "requested_amount": result["requested_amount"],
                }
            ),
        )
        if alert_result is not None:
            if alert_result.get("alert_created"):
                st.success(
                    f"Alert #{alert_result.get('alert_id')} created. "
                    "Go to **Cases** to assign an owner and read next steps."
                )
            elif alert_result.get("deduplicated"):
                st.info(
                    f"This shortfall is already alert "
                    f"#{alert_result.get('alert_id')} — no duplicate created."
                )
            else:
                st.info(alert_result.get("reason"))

    render_technical_detail(result)


# ── Network support ───────────────────────────────────────────────────────────

def _render_network(client: BackendClient) -> None:
    st.markdown(
        "**Which nearby agents can cover a shortfall?**  \n"
        "Searches the Sylhet network for agents with enough float or cash."
    )

    clicked = render_recipe_cards(NETWORK_RECIPES, key_prefix="net")
    if clicked:
        _apply_recipe(clicked, prefix="net")
        st.rerun()

    st.divider()

    default_idx_agent = KNOWN_AGENT_CODES.index(
        st.session_state.get("net_agent", SAMPLE_AGENT_CODE)
    ) if st.session_state.get("net_agent") in KNOWN_AGENT_CODES else 0

    default_idx_provider = KNOWN_PROVIDER_CODES.index(
        st.session_state.get("net_provider", "NAGAD_SIM")
    ) if st.session_state.get("net_provider") in KNOWN_PROVIDER_CODES else 1

    default_tx_idx = TRANSACTION_TYPES.index(
        st.session_state.get("net_tx_type", "cash_in")
    ) if st.session_state.get("net_tx_type") in TRANSACTION_TYPES else 0

    default_amount = float(st.session_state.get("net_amount", 80000.0))

    with st.form("network_support_form"):
        col_a, col_b = st.columns(2)
        requesting_agent = col_a.selectbox(
            "Agent that needs help",
            KNOWN_AGENT_CODES,
            index=default_idx_agent,
            format_func=agent_display_name,
        )
        provider_code = col_b.selectbox(
            "Provider",
            KNOWN_PROVIDER_CODES,
            index=default_idx_provider,
            format_func=provider_label,
            key="network_provider",
        )
        col_c, col_d, col_e = st.columns(3)
        transaction_type = col_c.selectbox(
            "Transaction type",
            TRANSACTION_TYPES,
            index=default_tx_idx,
            format_func=lambda v: (
                "Cash-in" if v == "cash_in" else "Cash-out"
            ),
            key="network_tx_type",
        )
        amount = col_d.number_input(
            "Amount (৳)",
            min_value=1.0,
            value=default_amount,
            step=1000.0,
            key="network_amount",
        )
        max_km = col_e.number_input(
            "Search radius (km)",
            min_value=0.5,
            max_value=100.0,
            value=10.0,
            step=0.5,
        )
        submitted = st.form_submit_button("Find nearby support", type="primary")

    if submitted:
        result = run_api_call(
            "Searching the agent network…",
            lambda: client.find_network_support(
                {
                    "requesting_agent_code": requesting_agent,
                    "provider_code": provider_code,
                    "transaction_type": transaction_type,
                    "amount": amount,
                    "max_distance_km": max_km,
                }
            ),
        )
        if result is not None:
            st.session_state["network_result"] = result
            st.session_state["network_result_agent"] = requesting_agent
            st.session_state["network_result_provider"] = provider_code

    stored = st.session_state.get("network_result")
    if stored is None:
        st.caption(
            "Pick the scenario card above or fill in the form, then "
            "click **Find nearby support**."
        )
        return

    _render_network_result(
        stored,
        st.session_state.get("network_result_agent", requesting_agent),
        st.session_state.get("network_result_provider", provider_code),
        client,
    )


def _render_network_result(
    result: dict,
    requesting_agent: str,
    provider_code: str,
    client: BackendClient,
) -> None:
    local_ok = result.get("local_serviceable", False)
    local_avail = result.get("local_available_amount", 0)
    shortfall = result.get("shortfall", 0)
    req_amount = result.get("requested_amount", 0)
    candidates = result.get("candidates", [])
    provider = provider_label(provider_code)
    agent_name = next(
        (v for k, v in [
            ("AGENT-SYL-001", "Zindabazar"),
            ("AGENT-SYL-002", "Ambarkhana"),
            ("AGENT-SYL-003", "Bondor"),
            ("AGENT-SYL-004", "Shibgonj"),
        ] if k == requesting_agent),
        requesting_agent,
    )

    if local_ok:
        st.markdown(
            f'<div class="result-banner pass">'
            f"✓ {agent_name} can serve locally — {money(local_avail)} {provider} float available"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="result-banner warn">'
            f"⚠ {agent_name} only has {money(local_avail)} {provider} float — "
            f"needs {money(req_amount)}, short by {money(shortfall)}"
            f"</div>",
            unsafe_allow_html=True,
        )

    if result.get("explanation"):
        st.write(result["explanation"])
    if result.get("recommended_action"):
        st.markdown(f"**Recommended action:** {result['recommended_action']}")

    if candidates:
        st.markdown("#### Nearby agents who can help")
        rows = []
        for c in candidates:
            status = c.get("recommendation_status", "")
            tag = (
                "✓ Recommended"
                if status == "RECOMMENDED"
                else ("⚠ Confirm first" if status == "REQUIRES_CONFIRMATION" else "× Insufficient")
            )
            rows.append(
                {
                    "Branch": c.get("name", c.get("agent_code", "")),
                    "Distance": f"{c.get('distance_km', '?')} km",
                    f"{provider_label(result.get('provider_code'))} float": money(c.get("resource_balance")),
                    "Can cover?": "Yes" if c.get("can_cover_shortfall") else "No",
                    "Status": tag,
                    "Feed": freshness_label(c.get("freshness_state")),
                    "Why": c.get("explanation", "")[:80],
                }
            )
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            width="stretch",
        )

        _render_network_capacity_chart(
            candidates=candidates,
            shortfall=shortfall,
            provider=provider,
        )
        _render_one_click_support(
            candidates=candidates,
            result=result,
            requesting_agent=requesting_agent,
            client=client,
        )
    elif not local_ok:
        st.warning("No nearby agents found within the search radius.")

    render_technical_detail(result)


def _render_network_capacity_chart(
    *,
    candidates: list[dict],
    shortfall,
    provider: str,
) -> None:
    """Bar chart: each candidate's usable capacity vs the shortfall."""

    chart_rows = []
    for c in candidates:
        try:
            capacity = float(c.get("supportable_capacity") or 0)
        except (TypeError, ValueError):
            capacity = 0.0
        name = str(c.get("name") or c.get("agent_code") or "")
        name = name.replace("Synthetic ", "").replace(" Agent", "")
        chart_rows.append({"Branch": name, "Amount (৳)": capacity, "Type": "Usable capacity"})

    try:
        shortfall_amount = float(shortfall or 0)
    except (TypeError, ValueError):
        shortfall_amount = 0.0
    if shortfall_amount > 0:
        chart_rows.append(
            {
                "Branch": "NEEDED",
                "Amount (৳)": shortfall_amount,
                "Type": "Shortfall to cover",
            }
        )

    if not chart_rows:
        return

    st.markdown(f"**{provider} capacity available nearby vs the shortfall**")
    frame = pd.DataFrame(chart_rows)
    st.bar_chart(
        frame,
        x="Branch",
        y="Amount (৳)",
        color="Type",
        height=260,
    )


def _render_one_click_support(
    *,
    candidates: list[dict],
    result: dict,
    requesting_agent: str,
    client: BackendClient,
) -> None:
    """One-click agent-to-agent support request from a candidate row."""

    viable = [
        c for c in candidates if c.get("can_cover_shortfall")
    ]
    if not viable:
        return

    st.markdown("#### Ask a peer agent for support")
    st.caption(
        "Creates a formal agent-to-agent support request that operations "
        "can accept, escalate, or resolve. No money moves automatically."
    )

    cols = st.columns(len(viable))
    for col, candidate in zip(cols, viable):
        code = str(candidate.get("agent_code") or "")
        name = str(candidate.get("name") or code)
        name = name.replace("Synthetic ", "").replace(" Agent", "")
        recommended = (
            candidate.get("recommendation_status") == "RECOMMENDED"
        )
        label = (
            f"Request from {name}"
            + (" (recommended)" if recommended else " (confirm first)")
        )
        with col:
            if st.button(
                label,
                key=f"support_req_{code}",
                type="primary" if recommended else "secondary",
            ):
                shortfall_amount = float(result.get("shortfall") or 0)
                created = run_api_call(
                    f"Creating support request to {name}…",
                    lambda: client.create_support_request(
                        {
                            "requesting_agent_code": requesting_agent,
                            "supporting_agent_code": code,
                            "provider_code": result.get("provider_code"),
                            "transaction_type": result.get(
                                "transaction_type", "cash_in"
                            ),
                            "requested_amount": shortfall_amount,
                            "reason": (
                                "Float shortfall found by network search — "
                                f"short by ৳{shortfall_amount:,.0f}."
                            ),
                            "created_by": "ops.coordinator",
                        }
                    ),
                )
                if created is not None:
                    st.session_state["selected_support_request"] = created
                    st.success(
                        f"Support request #{created.get('id')} sent to "
                        f"{name}. Track it under **Advanced dashboards → "
                        "Support only**, or in **Cases**."
                    )


# ── Forecast ──────────────────────────────────────────────────────────────────

def _render_forecast(client: BackendClient) -> None:
    st.markdown(
        "**How long before this provider's float hits the safety threshold?**  \n"
        "Uses actual transaction history to estimate consumption rate."
    )

    clicked = render_recipe_cards(FORECAST_RECIPES, key_prefix="fcast")
    if clicked:
        _apply_recipe(clicked, prefix="fcast")
        st.rerun()

    st.divider()

    default_agent = st.session_state.get("fcast_agent", SAMPLE_AGENT_CODE)
    default_prov = st.session_state.get("fcast_provider", "NAGAD_SIM")
    default_resource = st.session_state.get("fcast_resource", "provider_float")
    default_scenario = st.session_state.get("fcast_scenario", SAMPLE_SCENARIO_ID)
    default_lookback = int(st.session_state.get("fcast_lookback", 6))

    default_idx_agent = (
        KNOWN_AGENT_CODES.index(default_agent)
        if default_agent in KNOWN_AGENT_CODES
        else 0
    )
    default_idx_prov = (
        KNOWN_PROVIDER_CODES.index(default_prov)
        if default_prov in KNOWN_PROVIDER_CODES
        else 0
    )
    resource_options = RESOURCE_TYPES
    default_idx_resource = (
        resource_options.index(default_resource)
        if default_resource in resource_options
        else 0
    )

    with st.form("forecast_form"):
        col_a, col_b, col_c = st.columns(3)
        agent_code = col_a.selectbox(
            "Agent",
            KNOWN_AGENT_CODES,
            index=default_idx_agent,
            format_func=agent_display_name,
            key="forecast_agent",
        )
        provider_code = col_b.selectbox(
            "Provider",
            KNOWN_PROVIDER_CODES,
            index=default_idx_prov,
            format_func=provider_label,
            key="forecast_provider",
        )
        resource_type = col_c.selectbox(
            "Resource type",
            resource_options,
            index=default_idx_resource,
            format_func=lambda v: (
                "Provider electronic float"
                if v == "provider_float"
                else "Shared physical cash"
            ),
        )
        st.caption(
            f"Scenario in use: **{default_scenario or 'all'}** "
            f"(set by the scenario selector at the top). "
            f"Lookback window: last {default_lookback} hours of transactions."
        )
        submitted = st.form_submit_button("Estimate runway", type="primary")

    if not submitted:
        return

    payload = {
        "agent_code": agent_code,
        "resource_type": resource_type,
        "provider_code": optional_text(provider_code),
        "scenario_id": optional_text(default_scenario),
        "lookback_hours": default_lookback,
        "warning_threshold_hours": 8.0,
    }

    result = run_api_call(
        "Estimating liquidity runway…",
        lambda: client.forecast_liquidity_runway(payload),
    )

    if result is None:
        return

    _render_forecast_result(result, provider_code)


def _render_forecast_result(result: dict, provider_code: str) -> None:
    risk = result.get("risk_level", "")
    runway = result.get("runway_hours")
    current_bal = result.get("current_balance", 0)
    safety_thresh = result.get("safety_threshold", 0)
    net_per_hour = result.get("net_consumption_per_hour", 0)
    provider = provider_label(provider_code)
    breach_time = result.get("estimated_threshold_breach_time")
    txn_count = result.get("completed_transaction_count", 0)

    css_class = (
        "fail" if risk in ("HIGH", "CRITICAL")
        else "warn" if risk in ("MEDIUM", "LOW")
        else "pass"
    )
    icon = (
        "🔴" if risk in ("CRITICAL", "HIGH")
        else "🟡" if risk == "MEDIUM"
        else "🟢"
    )

    # Runway sentence
    if runway is not None:
        runway_txt = f"~{float(runway):.1f} hours remaining"
    else:
        runway_txt = "cannot estimate (insufficient history)"

    st.markdown(
        f'<div class="result-banner {css_class}">'
        f"{icon} {risk.replace('_', ' ')} RISK — {provider} float: "
        f"{money(current_bal)} · {runway_txt}"
        f"</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Current balance", money(current_bal))
    col2.metric("Safety threshold", money(safety_thresh))
    col3.metric(
        "Burn rate / hour",
        money(net_per_hour) if net_per_hour else "—",
    )

    _render_runway_chart(
        current_balance=current_bal,
        safety_threshold=safety_thresh,
        net_per_hour=net_per_hour,
        provider=provider,
    )

    if breach_time:
        st.markdown(
            f"At this burn rate, the safety threshold will be reached "
            f"**around {breach_time[:16].replace('T', ' ')} UTC**."
        )
    elif runway is None:
        st.markdown(
            f"Only **{txn_count} transactions** found in the lookback window. "
            "Need more transaction history to estimate runway."
        )

    if result.get("warning_message"):
        st.warning(result["warning_message"])

    factors = result.get("explanation_factors", [])
    if factors:
        st.markdown("**How this was calculated:**")
        for factor in factors:
            st.write(f"- {factor}")

    render_technical_detail(result)


def _render_runway_chart(
    *,
    current_balance,
    safety_threshold,
    net_per_hour,
    provider: str,
) -> None:
    """Line chart: projected float vs safety threshold over 24 hours."""

    try:
        balance = float(current_balance or 0)
        threshold = float(safety_threshold or 0)
        burn = float(net_per_hour or 0)
    except (TypeError, ValueError):
        return
    if balance <= 0:
        return

    hours = list(range(0, 25))
    projected = [max(balance - burn * h, 0.0) for h in hours]
    frame = pd.DataFrame(
        {
            "Hours from now": hours,
            f"Projected {provider} float (৳)": projected,
            "Safety threshold (৳)": [threshold] * len(hours),
        }
    )

    st.markdown("**Projected float over the next 24 hours**")
    st.line_chart(
        frame,
        x="Hours from now",
        height=260,
    )
    if burn <= 0:
        st.caption(
            "No net consumption detected in the lookback window, so the "
            "projection stays flat."
        )


# ── Anomaly ───────────────────────────────────────────────────────────────────

def _render_anomaly(client: BackendClient) -> None:
    st.markdown(
        "**Are there unusual transaction patterns in the last hour?**  \n"
        "Looks for repeated amounts and velocity spikes against a baseline."
    )

    clicked = render_recipe_cards(ANOMALY_RECIPES, key_prefix="anom")
    if clicked:
        _apply_recipe(clicked, prefix="anom")
        st.rerun()

    st.divider()

    default_agent = st.session_state.get("anom_agent", SAMPLE_AGENT_CODE)
    default_prov = st.session_state.get("anom_provider", "BKASH_SIM")
    default_scenario = st.session_state.get(
        "anom_scenario",
        st.session_state.get("scenario_id", SAMPLE_SCENARIO_ID),
    )

    default_idx_agent = (
        KNOWN_AGENT_CODES.index(default_agent)
        if default_agent in KNOWN_AGENT_CODES
        else 0
    )
    default_idx_prov = (
        KNOWN_PROVIDER_CODES.index(default_prov)
        if default_prov in KNOWN_PROVIDER_CODES
        else 0
    )

    with st.form("anomaly_form"):
        col_a, col_b = st.columns(2)
        agent_code = col_a.selectbox(
            "Agent",
            KNOWN_AGENT_CODES,
            index=default_idx_agent,
            format_func=agent_display_name,
            key="anomaly_agent",
        )
        provider_code = col_b.selectbox(
            "Provider",
            KNOWN_PROVIDER_CODES,
            index=default_idx_prov,
            format_func=provider_label,
            key="anomaly_provider",
        )
        st.caption(
            f"Scenario: **{default_scenario or 'all'}**. "
            "Window: last 60 min vs prior 60 min baseline. "
            "Flags repeated amounts (≥5 similar) or 2× velocity spike."
        )
        submitted = st.form_submit_button(
            "Check for unusual activity",
            type="primary",
        )

    if not submitted:
        return

    result = run_api_call(
        "Scanning for unusual patterns…",
        lambda: client.detect_anomaly(
            {
                "agent_code": agent_code,
                "provider_code": optional_text(provider_code),
                "scenario_id": optional_text(default_scenario),
            }
        ),
    )

    if result is None:
        return

    _render_anomaly_result(result, provider_code)


def _render_anomaly_result(result: dict, provider_code: str) -> None:
    detected = result.get("anomaly_detected", False)
    category = result.get("category") or "—"
    severity = result.get("severity", "")
    provider = provider_label(provider_code)
    repeated_count = result.get("repeated_transaction_count", 0)
    velocity_ratio = result.get("velocity_ratio")
    recent_count = result.get("recent_transaction_count", 0)
    baseline_count = result.get("baseline_transaction_count", 0)

    if detected:
        st.markdown(
            f'<div class="result-banner fail">'
            f"⚠ UNUSUAL ACTIVITY DETECTED — {provider}"
            f"</div>",
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns(3)
        col1.metric("Pattern", category.replace("_", " ").title())
        col2.metric("Priority", severity)
        col3.metric(
            "Recent vs baseline txns",
            f"{recent_count} / {baseline_count}",
        )

        _render_anomaly_chart(recent_count, baseline_count)

        if category == "repeated_amounts" and repeated_count:
            st.markdown(
                f"**{repeated_count} transactions** had similar amounts "
                f"(within ৳100 tolerance) in the last 60 minutes. "
                "This can indicate structured deposits."
            )
        if result.get("velocity_signal") and velocity_ratio:
            st.markdown(
                f"**Transaction velocity** was {float(velocity_ratio):.1f}× "
                "higher than the prior 60-minute baseline."
            )
    else:
        st.markdown(
            f'<div class="result-banner pass">'
            f"✓ No unusual activity — {provider} transactions look normal"
            f"</div>",
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        col1.metric("Recent transactions", recent_count)
        col2.metric("Baseline transactions", baseline_count)
        _render_anomaly_chart(recent_count, baseline_count)

    if result.get("warning_message"):
        st.caption(result["warning_message"])

    if result.get("uncertainty"):
        st.warning(str(result["uncertainty"]))

    if result.get("confidence") is not None:
        st.caption(f"Prototype confidence: {result['confidence']}")

    if result.get("decision"):
        st.caption(f"Decision: {str(result['decision']).replace('_', ' ')}")

    factors = result.get("explanation_factors", [])
    if factors:
        st.markdown("**What was checked:**")
        for factor in factors:
            st.write(f"- {factor}")

    if result.get("recommended_next_step"):
        st.markdown(
            f"**Recommended next step:** {result['recommended_next_step']}"
        )

    render_technical_detail(result)


def _render_anomaly_chart(recent_count, baseline_count) -> None:
    """Bar chart: last 60 min vs prior 60 min transaction volume."""

    try:
        recent = int(recent_count or 0)
        baseline = int(baseline_count or 0)
    except (TypeError, ValueError):
        return
    if recent == 0 and baseline == 0:
        return

    frame = pd.DataFrame(
        {
            "Window": ["Prior 60 min (baseline)", "Last 60 min"],
            "Transactions": [baseline, recent],
        }
    )
    st.markdown("**Transaction volume — last hour vs baseline**")
    st.bar_chart(
        frame,
        x="Window",
        y="Transactions",
        height=220,
    )


# ── Helper to apply recipe values to session state ────────────────────────────

def _apply_recipe(recipe: DemoRecipe, prefix: str) -> None:
    st.session_state[f"{prefix}_agent"] = recipe.agent_code
    st.session_state[f"{prefix}_provider"] = recipe.provider_code
    st.session_state[f"{prefix}_tx_type"] = recipe.transaction_type
    st.session_state[f"{prefix}_amount"] = recipe.amount
    st.session_state[f"{prefix}_resource"] = recipe.resource_type
    st.session_state[f"{prefix}_lookback"] = recipe.lookback_hours
    st.session_state[f"{prefix}_scenario"] = recipe.scenario_id
    st.session_state["scenario_id"] = recipe.scenario_id
    options = st.session_state.get("_scenario_options", {})
    matched_label = next(
        (
            label
            for label, sid in options.items()
            if sid == recipe.scenario_id
        ),
        None,
    )
    if matched_label:
        st.session_state["scenario_label"] = matched_label
    else:
        info = SCENARIO_REGISTRY.get(recipe.scenario_id)
        st.session_state["scenario_label"] = (
            f"{info.label} ({recipe.scenario_id})"
            if info
            else recipe.scenario_id
        )
