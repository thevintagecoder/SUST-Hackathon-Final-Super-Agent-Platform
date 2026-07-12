"""Shared Streamlit UI helpers for backend-backed views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from html import escape
from typing import Any, Callable

import numpy as np
import pandas as pd
import streamlit as st

from frontend.api.client import BackendAPIError, BackendClient
from frontend.components.scenarios import SCENARIO_REGISTRY, ScenarioInfo


# ── Known synthetic identifiers ──────────────────────────────────────────────

SAMPLE_AGENT_CODE = "AGENT-SYL-001"
DEMO_MAIN_AGENT = "AGENT-SYL-001"
SAMPLE_PROVIDER_CODE = "NAGAD_SIM"
SAMPLE_SCENARIO_ID = "NETWORK-001"

KNOWN_AGENT_CODES = [
    "AGENT-SYL-001",
    "AGENT-SYL-002",
    "AGENT-SYL-003",
    "AGENT-SYL-004",
]

KNOWN_PROVIDER_CODES = [
    "BKASH_SIM",
    "NAGAD_SIM",
    "ROCKET_SIM",
]

ALERT_STATUSES = [
    "",
    "OPEN",
    "ACKNOWLEDGED",
    "ASSIGNED",
    "ESCALATED",
    "RESOLVED",
]

ALERT_TYPES = [
    "",
    "LIQUIDITY_RUNWAY",
    "ANOMALY_REVIEW",
    "STALE_DATA",
    "SERVICEABILITY_SHORTFALL",
]

SUPPORT_STATUSES = [
    "",
    "pending",
    "accepted",
    "rejected",
    "escalated",
    "resolved",
    "cancelled",
]

TRANSACTION_TYPES = ["cash_in", "cash_out"]
RESOURCE_TYPES = ["provider_float", "physical_cash"]

PROVIDER_LABELS = {
    "BKASH_SIM": "bKash",
    "NAGAD_SIM": "Nagad",
    "ROCKET_SIM": "Rocket",
}

# ── Human-readable label maps ────────────────────────────────────────────────

ALERT_TYPE_LABELS = {
    "LIQUIDITY_RUNWAY": "Float running low",
    "ANOMALY_REVIEW": "Unusual activity",
    "STALE_DATA": "Balance feed delayed",
    "SERVICEABILITY_SHORTFALL": "Cannot serve customer amount",
}

ALERT_STATUS_LABELS = {
    "OPEN": "New — needs review",
    "ACKNOWLEDGED": "Seen by operations",
    "ASSIGNED": "Owner assigned",
    "ESCALATED": "Escalated",
    "RESOLVED": "Resolved",
}

SEVERITY_LABELS = {
    "LOW": "Low",
    "MEDIUM": "Medium",
    "HIGH": "High",
    "CRITICAL": "Critical",
}

# ── Agent display names (real names from synthetic_data/scenarios.py) ─────────

AGENT_NAMES = {
    "AGENT-SYL-001": "Zindabazar branch",
    "AGENT-SYL-002": "Ambarkhana branch",
    "AGENT-SYL-003": "Bondor branch",
    "AGENT-SYL-004": "Shibgonj branch",
}


# ── Demo recipe dataclass ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class DemoRecipe:
    """Pre-filled form values for one testable scenario."""

    title: str
    scenario_id: str
    agent_code: str
    provider_code: str
    transaction_type: str
    amount: float
    resource_type: str
    lookback_hours: int
    expect: str
    css_class: str


SERVICEABILITY_RECIPES: list[DemoRecipe] = [
    DemoRecipe(
        title="Nagad coordination — Zindabazar ৳80k cash-in",
        scenario_id="NETWORK-001",
        agent_code="AGENT-SYL-001",
        provider_code="NAGAD_SIM",
        transaction_type="cash_in",
        amount=80000.0,
        resource_type="provider_float",
        lookback_hours=6,
        expect="FAIL — only ৳20,000 Nagad float available",
        css_class="danger",
    ),
    DemoRecipe(
        title="bKash shortage — Zindabazar ৳50k cash-in",
        scenario_id="SHORTAGE-001",
        agent_code="AGENT-SYL-001",
        provider_code="BKASH_SIM",
        transaction_type="cash_in",
        amount=50000.0,
        resource_type="provider_float",
        lookback_hours=6,
        expect="FAIL — only ৳18,000 bKash float available",
        css_class="danger",
    ),
    DemoRecipe(
        title="Normal — all balances healthy ৳30k",
        scenario_id="NORMAL-001",
        agent_code="AGENT-SYL-001",
        provider_code="NAGAD_SIM",
        transaction_type="cash_in",
        amount=30000.0,
        resource_type="provider_float",
        lookback_hours=6,
        expect="PASS — ৳62,000 Nagad float available",
        css_class="ok",
    ),
]

FORECAST_RECIPES: list[DemoRecipe] = [
    DemoRecipe(
        title="Nagad runway — burns ৳7,500/hr",
        scenario_id="FORECAST-001",
        agent_code="AGENT-SYL-001",
        provider_code="NAGAD_SIM",
        transaction_type="cash_in",
        amount=0,
        resource_type="provider_float",
        lookback_hours=6,
        expect="HIGH risk — ~8 hours until threshold breach",
        css_class="danger",
    ),
    DemoRecipe(
        title="Normal — stable consumption",
        scenario_id="NORMAL-001",
        agent_code="AGENT-SYL-001",
        provider_code="NAGAD_SIM",
        transaction_type="cash_in",
        amount=0,
        resource_type="provider_float",
        lookback_hours=6,
        expect="STABLE or LOW risk — no shortage signal",
        css_class="ok",
    ),
]

ANOMALY_RECIPES: list[DemoRecipe] = [
    DemoRecipe(
        title="Repeated bKash amounts — 5 identical cash-ins",
        scenario_id="REPEATED-001",
        agent_code="AGENT-SYL-001",
        provider_code="BKASH_SIM",
        transaction_type="cash_in",
        amount=0,
        resource_type="provider_float",
        lookback_hours=6,
        expect="ANOMALY — repeated_amounts pattern flagged",
        css_class="danger",
    ),
    DemoRecipe(
        title="Normal — no unusual activity",
        scenario_id="NORMAL-001",
        agent_code="AGENT-SYL-001",
        provider_code="BKASH_SIM",
        transaction_type="cash_in",
        amount=0,
        resource_type="provider_float",
        lookback_hours=6,
        expect="CLEAN — no anomaly detected",
        css_class="ok",
    ),
]

NETWORK_RECIPES: list[DemoRecipe] = [
    DemoRecipe(
        title="Find who can cover ৳80k Nagad — Zindabazar is short",
        scenario_id="NETWORK-001",
        agent_code="AGENT-SYL-001",
        provider_code="NAGAD_SIM",
        transaction_type="cash_in",
        amount=80000.0,
        resource_type="provider_float",
        lookback_hours=6,
        expect="Ambarkhana (1.2 km, ৳120k Nagad) is recommended",
        css_class="warn",
    ),
]

# ── Caching helpers (1-min TTL to avoid repeated dashboard calls) ─────────────

@st.cache_data(ttl=60, show_spinner=False)
def cached_operations_dashboard(
    base_url: str,
    scenario_id: str | None,
    recent_alert_limit: int,
) -> dict[str, Any]:
    client = BackendClient(base_url=base_url)
    try:
        return client.operations_dashboard(
            scenario_id=scenario_id,
            recent_alert_limit=recent_alert_limit,
        )
    finally:
        client.close()


@st.cache_data(ttl=60, show_spinner=False)
def cached_management_dashboard(
    base_url: str,
    scenario_id: str | None,
) -> dict[str, Any]:
    client = BackendClient(base_url=base_url)
    try:
        return client.management_dashboard(scenario_id=scenario_id)
    finally:
        client.close()


@st.cache_data(ttl=60, show_spinner=False)
def cached_provider_dashboard(
    base_url: str,
    provider_code: str,
    scenario_id: str | None,
    recent_alert_limit: int,
) -> dict[str, Any]:
    client = BackendClient(base_url=base_url)
    try:
        return client.provider_dashboard(
            provider_code,
            scenario_id=scenario_id,
            recent_alert_limit=recent_alert_limit,
        )
    finally:
        client.close()


@st.cache_data(ttl=60, show_spinner=False)
def cached_list_alerts(
    base_url: str,
    scenario_id: str | None,
    limit: int,
) -> dict[str, Any]:
    client = BackendClient(base_url=base_url)
    try:
        return client.list_alerts(scenario_id=scenario_id, limit=limit)
    finally:
        client.close()


# ── Core helpers ──────────────────────────────────────────────────────────────

def localized_text(
    value: Any,
    *,
    language: str = "en",
) -> str:
    if isinstance(value, dict):
        return str(
            value.get(language)
            or value.get("en")
            or next(iter(value.values()), "")
        )
    if value is None:
        return ""
    return str(value)


def active_language() -> str:
    return st.session_state.get("language_code", "en")


def alert_type_label(value: str | None) -> str:
    if not value:
        return "Risk review"
    return ALERT_TYPE_LABELS.get(value, value.replace("_", " ").title())


def alert_status_label(value: str | None) -> str:
    if not value:
        return "Unknown"
    return ALERT_STATUS_LABELS.get(value, str(value).title())


def severity_label(value: str | None) -> str:
    if not value:
        return "Low"
    return SEVERITY_LABELS.get(value, str(value).title())


def agent_display_name(code: str | None) -> str:
    if not code:
        return ""
    name = AGENT_NAMES.get(code, code)
    return f"{name} ({code})"


def show_api_error(error: Exception) -> None:
    message = str(error)
    st.error(message)
    if "HTTP 404" in message:
        st.caption(
            "Check that the selected agent, provider, and scenario "
            "exist in the loaded synthetic dataset."
        )
    elif "HTTP 409" in message:
        st.caption(
            "Balance or transaction data is unavailable for this "
            "combination. Make sure you loaded the matching scenario."
        )


def run_api_call(
    label: str,
    call: Callable[[], dict[str, Any]],
) -> dict[str, Any] | None:
    try:
        with st.spinner(label):
            return call()
    except BackendAPIError as error:
        show_api_error(error)
        return None


def optional_text(value: str) -> str | None:
    cleaned = value.strip()
    return cleaned or None


def money(value: Any) -> str:
    if value is None or value == "":
        return "—"
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)
    return f"৳{amount:,.2f}"


def provider_label(code: str | None) -> str:
    if not code:
        return "All providers"
    return PROVIDER_LABELS.get(
        code,
        code.replace("_SIM", "").title(),
    )


def provider_css_class(code: str | None) -> str:
    return {
        "BKASH_SIM": "bkash",
        "NAGAD_SIM": "nagad",
    }.get(code, "other")


def freshness_label(value: str | None) -> str:
    labels = {
        "fresh": "Live balance",
        "delayed": "⚠ Delayed — verify",
        "conflicting": "⚠ Conflicting feed — verify",
        "missing": "⚠ Missing feed — verify",
        "stale": "⚠ Stale — verify before acting",
    }
    return labels.get(value or "", value or "Update time unavailable")


def format_timestamp(value: Any) -> str:
    if not value:
        return "Time unavailable"
    try:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except ValueError:
        return str(value)
    return parsed.strftime("%d %b, %I:%M %p")


PLACEHOLDER_BRANCH_LABELS = {
    "",
    "string",
    "null",
    "none",
    "undefined",
    "n/a",
    "na",
    "unknown",
}


def is_placeholder_branch_label(value: str | None) -> bool:
    """Return True when a branch label is safe to show on charts."""

    cleaned = str(value or "").strip()
    if not cleaned:
        return False
    return cleaned.lower() not in PLACEHOLDER_BRANCH_LABELS


def render_summary_metrics(items: list[tuple[str, str]]) -> None:
    """Render alert-style summary cards that wrap instead of truncating."""

    cards = []
    for label, value in items:
        display = str(value) if value not in (None, "") else "—"
        cards.append(
            (
                f'<div class="alert-summary-card" title="{escape(display)}">'
                f'<div class="alert-summary-label">{escape(label)}</div>'
                f'<div class="alert-summary-value">{escape(display)}</div>'
                "</div>"
            )
        )
    st.markdown(
        (
            '<div class="alert-summary-grid">'
            f"{''.join(cards)}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def metric_row(items: list[tuple[str, Any]]) -> None:
    if not items:
        return
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items):
        column.metric(label, value if value is not None else "—")


def safety_notice(text: str | None = None) -> None:
    message = text or (
        "Synthetic data only. No real money, no real accounts. "
        "Every alert requires human review before any action."
    )
    st.markdown(
        f'<div class="notice">{escape(message)}</div>',
        unsafe_allow_html=True,
    )


def render_scenario_context() -> None:
    """Show a short explanation of the currently selected scenario."""

    scenario_id = st.session_state.get("scenario_id")
    if not scenario_id:
        return

    info = SCENARIO_REGISTRY.get(scenario_id)
    if not info:
        return

    st.markdown(
        f'<div class="notice">'
        f"<b>{escape(info.label)}</b><br>"
        f"{escape(info.what_it_tests)}<br>"
        f"<em>{escape(info.interesting_result)}</em>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_recipe_cards(
    recipes: list[DemoRecipe],
    *,
    key_prefix: str,
) -> DemoRecipe | None:
    """Render clickable recipe cards; return the one clicked."""

    st.markdown(
        "<p style='color:var(--muted);font-size:.75rem;"
        "font-weight:800;letter-spacing:.1em;text-transform:uppercase;"
        "margin:0 0 .4rem'>Pick a test scenario or fill in below</p>",
        unsafe_allow_html=True,
    )
    cols = st.columns(len(recipes))
    for i, (col, recipe) in enumerate(zip(cols, recipes)):
        with col:
            info = SCENARIO_REGISTRY.get(recipe.scenario_id)
            scenario_label = info.label if info else recipe.scenario_id
            st.markdown(
                f'<div class="recipe-card {escape(recipe.css_class)}">'
                f'<div class="recipe-title">{escape(recipe.title)}</div>'
                f'<div class="recipe-desc">{escape(scenario_label)}</div>'
                f'<div class="recipe-expect">{escape(recipe.expect)}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "Use this scenario",
                key=f"{key_prefix}_recipe_{i}",
                type="secondary",
            ):
                return recipe
    return None


def render_technical_detail(
    payload: dict[str, Any] | list[Any] | None,
    *,
    label: str = "Technical detail (raw API response)",
) -> None:
    if payload is None:
        return
    with st.expander(label, expanded=False):
        st.json(payload)


def render_json_expander(
    title: str,
    payload: dict[str, Any],
    *,
    expanded: bool = False,
) -> None:
    render_technical_detail(payload, label=title)


def render_evidence_summary(evidence: dict[str, Any] | None) -> None:
    if not evidence:
        st.caption("No supporting evidence attached.")
        return
    for key, value in evidence.items():
        label = key.replace("_", " ").strip().title()
        if isinstance(value, dict):
            parts = [f"{k}: {v}" for k, v in value.items()]
            st.write(f"**{label}:** {', '.join(parts)}")
        elif isinstance(value, list):
            st.write(f"**{label}:**")
            for item in value:
                st.write(f"- {item}")
        else:
            st.write(f"**{label}:** {value}")


def render_balance_card(
    *,
    title: str,
    amount: Any,
    eyebrow: str,
    meta: str,
    css_class: str,
) -> None:
    st.markdown(
        (
            f'<div class="balance-card {escape(css_class)}">'
            f'<div class="card-eyebrow">{escape(eyebrow)}</div>'
            f'<div class="card-title">{escape(title)}</div>'
            f'<div class="card-amount">{escape(money(amount))}</div>'
            f'<div class="card-meta">{escape(meta)}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


SHORTFALL_UNASSIGNED_STATUS = (
    "Review nearby support options or refer the customer "
    "through a human-approved coordination process."
)


def _alert_work_status(alert: dict[str, Any]) -> str:
    owner = alert.get("assigned_to")
    status = alert.get("status")
    if status == "RESOLVED":
        return "Closed — kept for audit."
    if not owner:
        if alert.get("alert_type") == "SERVICEABILITY_SHORTFALL":
            return (
                localized_text(
                    alert.get("next_step"),
                    language=active_language(),
                )
                or SHORTFALL_UNASSIGNED_STATUS
            )
        return "Waiting for someone to take ownership."
    if status == "OPEN":
        return f"Assigned to {owner} — open the alert for next steps."
    return f"{alert_status_label(status)} · owner {owner}"


def navigate_to_peer_support(alert: dict[str, Any]) -> None:
    """Pre-fill Liquidity → Find support from a shortfall alert."""

    evidence = alert.get("evidence") or {}
    agent_code = alert.get("agent_code") or SAMPLE_AGENT_CODE
    provider_code = (
        alert.get("provider_code")
        or evidence.get("provider_code")
        or SAMPLE_PROVIDER_CODE
    )
    transaction_type = evidence.get("transaction_type", "cash_in")
    amount_raw = evidence.get("requested_amount")
    try:
        amount = float(str(amount_raw).replace(",", ""))
    except (TypeError, ValueError):
        amount = 80000.0

    st.session_state["current_page"] = "Liquidity"
    st.session_state["liquidity_tab"] = "network"
    st.session_state["net_agent"] = agent_code
    st.session_state["net_provider"] = provider_code
    st.session_state["net_tx_type"] = transaction_type
    st.session_state["net_amount"] = amount


def render_alert_card(
    alert: dict[str, Any],
    *,
    context_agent_code: str | None = None,
    next_step: str | None = None,
) -> None:
    severity_key = str(alert.get("severity") or "LOW").lower()
    title = (
        localized_text(
            alert.get("title"),
            language=active_language(),
        )
        or alert_type_label(alert.get("alert_type"))
    )
    agent_code = alert.get("agent_code") or context_agent_code
    owner = alert.get("assigned_to") or "Unassigned"
    provider = provider_label(alert.get("provider_code"))
    severity_text = severity_label(alert.get("severity"))
    status_text = alert_status_label(alert.get("status", "OPEN"))
    work_status = next_step or _alert_work_status(alert)

    agent_part = (
        f"<b>Agent:</b> {escape(AGENT_NAMES.get(agent_code, agent_code))}"
        if agent_code
        else ""
    )
    owner_part = f"<b>Owner:</b> {escape(str(owner))}"
    meta_agent = (
        f'<div class="alert-meta">{agent_part}'
        f'{"  &nbsp;  " if agent_part else ""}{owner_part}</div>'
    )

    st.markdown(
        (
            f'<div class="alert-card {escape(severity_key)}">'
            f'<div class="alert-title">{escape(title)}</div>'
            f'<div class="alert-meta">'
            f"{escape(severity_text)} · {escape(status_text)} · {escape(provider)}"
            f"</div>"
            f"{meta_agent}"
            f'<div class="alert-meta" style="margin-top:.25rem">'
            f"{escape(work_status)}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, detail: str) -> None:
    st.markdown(
        (
            '<div class="empty-state">'
            f"<b>{escape(title)}</b><br>{escape(detail)}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def numeric_sum(values: list[Any]) -> float:
    numbers = pd.to_numeric(
        pd.Series(values, dtype="object"),
        errors="coerce",
    ).fillna(0)
    return float(np.sum(numbers.to_numpy(dtype=float)))


def agent_options(
    operations_data: dict[str, Any] | None,
) -> list[str]:
    rows = (operations_data or {}).get("agent_risks", [])
    codes = [
        str(row["agent_code"])
        for row in rows
        if row.get("agent_code")
    ]
    return codes or KNOWN_AGENT_CODES
