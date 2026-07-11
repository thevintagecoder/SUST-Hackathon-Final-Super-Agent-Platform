"""Home: unified cash + provider balance view for one selected agent."""

from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from core.anomaly import detect_anomalies
from core.data_access import DataUnavailableError
from core.forecast import ProviderForecast, forecast_scenario
from frontend.components.badges import render_freshness_badge
from frontend.components.filters import get_repository, render_sidebar_filters
from frontend.components.metric_cards import format_currency


def provider_status(forecast: ProviderForecast) -> tuple[str, str]:
    """Return (label, badge color) — one clear status per provider."""

    if not math.isfinite(forecast.runway_hours):
        return "Healthy", "green"
    if forecast.runway_hours < forecast.warning_threshold_hours / 2:
        return "Critical", "red"
    if forecast.runway_hours < forecast.warning_threshold_hours:
        return "Pressure", "orange"
    return "Healthy", "green"


st.title("Home — Unified Balance View")

filters = render_sidebar_filters(include_providers=False)
if filters is None:
    st.stop()

repository = get_repository()

try:
    shared_cash = repository.shared_cash_for(
        filters.scenario.scenario_id,
        filters.agent_code,
    )
    forecasts = forecast_scenario(
        repository,
        filters.scenario.scenario_id,
        filters.agent_code,
    )
    flags = detect_anomalies(
        repository,
        filters.scenario.scenario_id,
        filters.agent_code,
    )
except DataUnavailableError as exc:
    st.error(str(exc))
    st.stop()

if not forecasts:
    st.info(f"No data yet for agent {filters.agent_code} in this scenario.")
    st.stop()

st.caption(
    f"Agent **{filters.agent_code}** · Scenario: "
    f"**{filters.scenario.name}** · Synthetic demonstration data"
)

cash_col, alert_col = st.columns([2, 1])
with cash_col:
    st.subheader("Shared physical cash")
    st.metric("Available shared cash", format_currency(shared_cash))
    st.caption(
        "Physical cash is shared across providers but electronic floats "
        "below are separate resources."
    )
with alert_col:
    st.subheader("Review queue")
    st.metric("Unusual-activity flags", len(flags))
    pressured = [item for item in forecasts if item.is_below_warning]
    st.metric("Providers below runway warning", len(pressured))

st.divider()
st.subheader("Provider electronic balances")

columns = st.columns(len(forecasts))
for column, forecast in zip(columns, forecasts, strict=True):
    with column:
        st.markdown(f"#### {forecast.provider_code}")
        st.metric(
            "Electronic balance",
            format_currency(forecast.current_balance),
        )
        label, color = provider_status(forecast)
        st.badge(label, color=color)
        render_freshness_badge(forecast.freshness)
        if math.isfinite(forecast.runway_hours):
            st.caption(f"Est. runway ~{forecast.runway_hours:.1f} h")
        else:
            st.caption("Balance not draining")
        if forecast.freshness != "fresh":
            st.caption(
                "Confidence reduced — provider feed delayed."
            )

balance_frame = pd.DataFrame(
    {
        "Provider": [item.provider_code for item in forecasts],
        "Balance": [item.current_balance for item in forecasts],
        "Status": [provider_status(item)[0] for item in forecasts],
    }
)
figure = px.bar(
    balance_frame,
    x="Balance",
    y="Provider",
    color="Status",
    orientation="h",
    title="Current provider balances (separate resources)",
    text="Balance",
    color_discrete_map={
        "Healthy": "#2ca02c",
        "Pressure": "#ff7f0e",
        "Critical": "#d62728",
    },
)
figure.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
figure.update_layout(height=320, showlegend=True)
st.plotly_chart(figure, use_container_width=True)

st.caption(
    "Statuses are derived from estimated runway versus the warning "
    "threshold. See the Liquidity Forecast page for details and "
    "confidence."
)
