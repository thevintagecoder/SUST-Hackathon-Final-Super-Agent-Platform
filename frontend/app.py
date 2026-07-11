"""Streamlit entry point for the Super Agent operations dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from frontend.config import API_BASE_URL, DATA_MODE, get_provider

st.set_page_config(
    page_title="Super Agent Liquidity & Risk Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Super Agent Liquidity & Risk Intelligence")

st.warning(
    "**Synthetic demonstration data** — This dashboard uses simulated "
    "provider balances and transactions for decision-support review only. "
    "It does not connect to real accounts or determine fraud."
)

if DATA_MODE == "mock":
    st.success(
        "Data mode: **mock** — showing local demonstration data from "
        "frontend/mock_data/. No backend is required."
    )
else:
    st.info(
        f"Data mode: **api** — reading live data from FastAPI at "
        f"{API_BASE_URL}. If the backend is unavailable, pages will show "
        "an error instead of falling back to mock data."
    )

with st.sidebar:
    st.subheader("Session")
    st.info(f"Data mode: **{DATA_MODE}**")

    try:
        overview = get_provider().get_overview()
        agent = overview.get("agent", {})
        st.metric("Agent", agent.get("code", "—"))
        st.caption(agent.get("name", ""))
        st.caption(f"Area: {agent.get('area', '—')}")
    except Exception as exc:
        st.error(str(exc))
        if DATA_MODE == "api":
            st.info(
                "The backend appears unavailable. Restart with "
                "DATA_MODE=mock to preview the UI without FastAPI."
            )

operations_page = st.Page(
    "pages/1_Operations_Overview.py",
    title="Operations Overview",
    icon="📋",
    default=True,
)
liquidity_page = st.Page(
    "pages/2_Liquidity.py",
    title="Liquidity",
    icon="💧",
)
anomaly_page = st.Page(
    "pages/3_Anomaly_Review.py",
    title="Anomaly Review",
    icon="🔍",
)
case_page = st.Page(
    "pages/4_Case_Management.py",
    title="Case Management",
    icon="📁",
)

navigation = st.navigation(
    [
        operations_page,
        liquidity_page,
        anomaly_page,
        case_page,
    ],
    position="top",
)
navigation.run()
