"""Liquidity Forecast: balance projection chart + plain-language panel."""

from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data_access import DataUnavailableError
from core.forecast import forecast_provider
from core.narrative import forecast_narrative
from frontend.components.badges import render_freshness_badge
from frontend.components.filters import get_repository, render_sidebar_filters

st.title("Liquidity Forecast")
st.caption(
    "Linear runway projection from recent net outflow. Decision support "
    "only — not a guarantee."
)

filters = render_sidebar_filters(include_providers=True, include_horizon=True)
if filters is None:
    st.stop()

if not filters.provider_codes:
    st.info("Select at least one provider in the sidebar to see forecasts.")
    st.stop()

repository = get_repository()

for provider_code in filters.provider_codes:
    try:
        forecast = forecast_provider(
            repository,
            filters.scenario.scenario_id,
            filters.agent_code,
            provider_code,
            horizon_hours=filters.horizon_hours,
        )
    except (DataUnavailableError, ValueError) as exc:
        st.warning(f"{provider_code}: {exc}")
        continue

    st.subheader(provider_code)

    if forecast.sample_size == 0:
        st.info(
            f"No transactions yet for {provider_code} in this scenario — "
            "showing the last known balance only."
        )

    if forecast.is_below_warning:
        st.error(forecast_narrative(forecast, "en"))
    else:
        st.success(forecast_narrative(forecast, "en"))

    if forecast.freshness != "fresh":
        st.warning(
            "Confidence reduced — the provider feed is "
            f"{forecast.freshness}. Treat this projection as provisional "
            "until the feed recovers."
        )

    history = forecast.timeline.loc[forecast.timeline["kind"] == "history"]
    projection = forecast.timeline.loc[forecast.timeline["kind"] == "forecast"]

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=history["time"],
            y=history["balance"],
            mode="lines+markers",
            name="Observed balance",
            line={"color": "#1f77b4"},
        )
    )
    if not projection.empty:
        bridge = pd.concat([history.tail(1), projection], ignore_index=True)
        figure.add_trace(
            go.Scatter(
                x=bridge["time"],
                y=bridge["balance"],
                mode="lines",
                name="Projected balance",
                line={"color": "#ff7f0e", "dash": "dash"},
            )
        )
    if forecast.projected_low_time is not None:
        figure.add_vline(
            x=forecast.projected_low_time,
            line_dash="dot",
            line_color="red",
        )
        figure.add_annotation(
            x=forecast.projected_low_time,
            y=0,
            text="Projected depletion",
            showarrow=True,
            arrowhead=1,
        )
    figure.update_layout(
        title=f"{provider_code} balance — observed and projected",
        xaxis_title="Time (UTC)",
        yaxis_title="Electronic balance",
        height=380,
    )
    st.plotly_chart(figure, use_container_width=True)

    detail_cols = st.columns(4)
    detail_cols[0].metric(
        "Net outflow / hour",
        f"{forecast.net_outflow_per_hour:,.0f}",
    )
    detail_cols[1].metric(
        "Estimated runway",
        "∞"
        if not math.isfinite(forecast.runway_hours)
        else f"{forecast.runway_hours:.1f} h",
    )
    detail_cols[2].metric("Confidence", f"{forecast.confidence * 100:.0f}%")
    detail_cols[3].metric("Sample size", forecast.sample_size)
    render_freshness_badge(forecast.freshness)

    with st.expander("Evidence window"):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Window hours": round(forecast.window_hours, 2),
                        "Sample size": forecast.sample_size,
                        "Volatility": round(forecast.volatility, 2),
                        "As of": forecast.as_of.isoformat(),
                    }
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.divider()
