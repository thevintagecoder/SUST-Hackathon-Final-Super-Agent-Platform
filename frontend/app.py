"""Streamlit entry point for the Super Agent operations dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from frontend.config import API_BASE_URL, DATA_MODE

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

st.caption(
    "Analytics pages (Home, Liquidity Forecast, Anomaly Alerts, Agent "
    "Risk Explorer) compute directly from the synthetic scenario dataset "
    "via the shared core/ package."
)

if DATA_MODE == "mock":
    st.success(
        "Data mode: **mock** — case-management workflow data comes from "
        "frontend/mock_data/. No backend is required."
    )
else:
    st.info(
        f"Data mode: **api** — case-management workflow data is read from "
        f"FastAPI at {API_BASE_URL}. If the backend is unavailable, that "
        "page shows an error instead of falling back to mock data."
    )

with st.sidebar:
    st.subheader("Session")
    st.info(f"Data mode: **{DATA_MODE}**")

home_page = st.Page(
    "pages/Home.py",
    title="Home",
    icon="🏠",
    default=True,
)
forecast_page = st.Page(
    "pages/1_Liquidity_Forecast.py",
    title="Liquidity Forecast",
    icon="💧",
)
anomaly_page = st.Page(
    "pages/2_Anomaly_Alerts.py",
    title="Anomaly Alerts",
    icon="🔍",
)
risk_page = st.Page(
    "pages/3_Agent_Risk_Explorer.py",
    title="Agent Risk Explorer",
    icon="🧭",
)
case_page = st.Page(
    "pages/4_Admin_Case_Management.py",
    title="Admin Case Management",
    icon="📁",
)

navigation = st.navigation(
    [
        home_page,
        forecast_page,
        anomaly_page,
        risk_page,
        case_page,
    ],
    position="top",
)
navigation.run()
