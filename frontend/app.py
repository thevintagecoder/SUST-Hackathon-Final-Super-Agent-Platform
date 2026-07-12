"""Streamlit entry point for the field-agent liquidity desk."""

from __future__ import annotations

import os
import sys
from html import escape
from pathlib import Path

# Ensure project root is on sys.path when Streamlit runs this file.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from frontend.api.client import BackendAPIError, BackendClient
from frontend.components.common import SAMPLE_SCENARIO_ID
from frontend.components.scenarios import SCENARIO_REGISTRY
from frontend.components.styles import apply_app_styles
from frontend.views.agent_dashboard import render_agent_dashboard
from frontend.views.alerts import render_alerts
from frontend.views.cases import render_cases
from frontend.views.evaluation_dashboard import (
    render_evaluation_dashboard,
)
from frontend.views.overview import render_overview
from frontend.views.operations_dashboard import (
    render_operations_dashboard,
)
from frontend.views.provider_dashboard import (
    render_provider_dashboard,
)
from frontend.views.support_requests import render_support_requests
from frontend.views.tools import render_anomalies, render_liquidity


DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"

MAIN_PAGES = {
    "Agent desk": render_agent_dashboard,
    "Liquidity": render_liquidity,
    "Anomalies": render_anomalies,
    "Cases": render_cases,
}

# Stakeholder / role-filter views (agent-first ordering).
STAKEHOLDER_PAGES = {
    "Agent desk": render_agent_dashboard,
    "Provider": render_provider_dashboard,
    "Operations": render_operations_dashboard,
    "Alerts only": render_alerts,
    "Support only": render_support_requests,
    "Model checks": render_evaluation_dashboard,
}

# Network overview is reachable from Agent desk; not a primary nav tab.
EXTRA_PAGES = {
    "Network": render_overview,
}

ALL_PAGES = {**MAIN_PAGES, **EXTRA_PAGES}

NAV_ITEMS = [
    ("Agent desk", "👤"),
    ("Liquidity", "💵"),
    ("Anomalies", "🔍"),
    ("Cases", "📋"),
]

DEFAULT_PAGE = "Agent desk"

SITE_TITLE = "Super Agent Liquidity and Risk Intelligence Platform"

DB_OPTIONAL_PAGES = {"Model checks"}


def _scenario_options() -> dict[str, str | None]:
    """Build human-readable scenario labels → raw IDs."""

    options: dict[str, str | None] = {"All scenarios": None}
    for sid, info in SCENARIO_REGISTRY.items():
        options[f"{info.label} ({sid})"] = sid
    return options


SCENARIO_OPTIONS = _scenario_options()

LANGUAGE_OPTIONS = {
    "English": "en",
    "বাংলা": "bn",
    "Banglish": "bn_latn",
}


def get_backend_base_url() -> str:
    """Return the configured FastAPI base URL."""

    return os.getenv(
        "FASTAPI_BASE_URL",
        DEFAULT_BACKEND_URL,
    ).strip().rstrip("/") or DEFAULT_BACKEND_URL


@st.cache_resource
def get_backend_client(base_url: str) -> BackendClient:
    """Create one shared backend API client."""

    return BackendClient(base_url=base_url)


def _render_site_title() -> None:
    """Render the platform name above page content."""

    st.markdown(
        (
            '<div class="site-title-wrap">'
            f'<div class="site-title">{escape(SITE_TITLE)}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def _render_bottom_nav() -> None:
    """Render four-tab field-agent navigation."""

    current_page = st.session_state.get("current_page", DEFAULT_PAGE)

    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    cols = st.columns(4)
    for col, (page, icon) in zip(cols, NAV_ITEMS):
        button_type = (
            "primary" if page == current_page else "secondary"
        )
        label = f"{icon} {page}"
        if col.button(
            label,
            key=f"nav_{page}",
            type=button_type,
            use_container_width=True,
        ):
            st.session_state["current_page"] = page
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


st.set_page_config(
    page_title=SITE_TITLE,
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_app_styles()

backend_base_url = get_backend_base_url()
backend_client = get_backend_client(backend_base_url)

api_ok = False
database_ok = False
connection_error = ""

try:
    api_ok = backend_client.health().get("status") == "ok"
except BackendAPIError as error:
    connection_error = str(error)

if api_ok:
    try:
        database_ok = (
            backend_client.health_database().get("status") == "ok"
        )
    except BackendAPIError as error:
        connection_error = str(error)

api_class = "ok" if api_ok else "bad"
db_class = "ok" if database_ok else "bad"
st.markdown(
    (
        '<div class="status-row">'
        f'<span class="status-pill {api_class}">'
        f"● API {'online' if api_ok else 'offline'}</span>"
        f'<span class="status-pill {db_class}">'
        f"● Data {'ready' if database_ok else 'unavailable'}</span>"
        "</div>"
    ),
    unsafe_allow_html=True,
)

_render_site_title()
_render_bottom_nav()

with st.container(border=True):
    context_cols = st.columns([1.4, 1.2, 2.4])
    scenario_options_list = list(SCENARIO_OPTIONS)
    saved_label = st.session_state.get("scenario_label")
    if saved_label in scenario_options_list:
        default_scenario_idx = scenario_options_list.index(saved_label)
    else:
        default_scenario_idx = next(
            (
                i for i, k in enumerate(scenario_options_list)
                if SAMPLE_SCENARIO_ID in k
            ),
            1,
        )
    scenario_label = context_cols[0].selectbox(
        "Active scenario",
        scenario_options_list,
        index=default_scenario_idx,
        help=(
            "Filters alerts and check results to this test scenario. "
            "Balances come from whichever scenario was last loaded "
            "into PostgreSQL."
        ),
    )
    language_label = context_cols[1].selectbox(
        "Alert text language",
        list(LANGUAGE_OPTIONS),
        index=list(LANGUAGE_OPTIONS).index(
            st.session_state.get("language_label", "English")
        )
        if st.session_state.get("language_label") in LANGUAGE_OPTIONS
        else 0,
    )
    scenario_id_selected = SCENARIO_OPTIONS.get(scenario_label)
    if scenario_id_selected:
        info = SCENARIO_REGISTRY.get(scenario_id_selected)
        hint = info.what_it_tests if info else ""
    else:
        hint = "Showing all scenarios. Pick one above for a focused demo."
    context_cols[2].caption(hint)

st.session_state["scenario_label"] = scenario_label
st.session_state["scenario_id"] = SCENARIO_OPTIONS[scenario_label]
st.session_state["language_label"] = language_label
st.session_state["language_code"] = LANGUAGE_OPTIONS[language_label]
st.session_state["_scenario_options"] = SCENARIO_OPTIONS

page_name = st.session_state.get("current_page", DEFAULT_PAGE)
needs_database = page_name not in DB_OPTIONAL_PAGES

if not api_ok:
    st.error(
        connection_error
        or "The FastAPI backend is not available."
    )
    st.code(
        "python -m uvicorn backend.app.main:app --reload",
        language="bash",
    )
    st.stop()

if needs_database and not database_ok:
    st.error(
        connection_error
        or "PostgreSQL is not available for this page."
    )
    st.caption(
        "Model checks can run with API only. Other pages need "
        "migrations and synthetic data loaded."
    )
    st.code(
        "python -m backend.app.data_loading.synthetic_loader "
        "--scenario NETWORK-001",
        language="bash",
    )
    st.stop()

if not database_ok and page_name in DB_OPTIONAL_PAGES:
    st.warning(
        "Database is offline. You can still view Model checks; "
        "live balances and alerts are unavailable."
    )

if page_name in ALL_PAGES:
    ALL_PAGES[page_name](backend_client)
else:
    st.session_state["current_page"] = DEFAULT_PAGE
    MAIN_PAGES[DEFAULT_PAGE](backend_client)
