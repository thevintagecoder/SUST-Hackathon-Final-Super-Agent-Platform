"""Liquidity runway and confidence dashboard page."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from frontend.components.alert_card import (
    format_confidence,
    render_uncertainty_callout,
)
from frontend.components.badges import render_freshness_badge
from frontend.config import get_active_data_mode, get_provider

st.title("Liquidity")
st.caption(
    f"Provider runway, confidence, and evidence window. "
    f"Data mode: **{get_active_data_mode()}**"
)

try:
    data_provider = get_provider()
    overview = data_provider.get_overview()
    liquidity = data_provider.get_liquidity(overview["agent"]["code"])
except Exception as exc:
    st.error(str(exc))
    st.stop()

positions = liquidity["positions"]
st.subheader(f"Agent {liquidity['agent_code']}")

for position in positions:
    st.markdown(f"### {position['resource']}")
    metric_cols = st.columns(4)
    metric_cols[0].metric(
        "Current balance",
        f"{position['current_balance']:,.2f}",
    )
    metric_cols[1].metric(
        "Net outflow / hour",
        f"{position['recent_net_outflow_per_hour']:,.2f}",
    )
    metric_cols[2].metric(
        "Estimated runway",
        f"{position['estimated_runway_hours']:.2f} h",
    )
    metric_cols[3].metric(
        "Warning threshold",
        f"{position['warning_threshold_hours']:.2f} h",
    )

    render_freshness_badge(position["freshness"])
    st.info(format_confidence(position["confidence"]))

    if position["freshness"] in {"delayed", "stale"}:
        render_uncertainty_callout(
            position["freshness"],
            "Delayed provider feeds can suppress strong recommendations.",
        )

    evidence = position["evidence"]
    st.markdown("**Evidence window**")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Window hours": evidence["window_hours"],
                    "Sample size": evidence["sample_size"],
                    "Volatility": evidence["volatility"],
                }
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.divider()

hours = list(
    range(
        0,
        int(max(position["estimated_runway_hours"] for position in positions)) + 2,
    )
)
runway_rows = []
for hour in hours:
    for position in positions:
        remaining = max(position["estimated_runway_hours"] - hour, 0)
        runway_rows.append(
            {
                "hour": hour,
                "resource": position["resource"],
                "remaining_runway_hours": remaining,
                "warning_threshold_hours": position["warning_threshold_hours"],
            }
        )

runway_chart = pd.DataFrame(runway_rows)
figure = go.Figure()
for resource in runway_chart["resource"].unique():
    subset = runway_chart[runway_chart["resource"] == resource]
    figure.add_trace(
        go.Scatter(
            x=subset["hour"],
            y=subset["remaining_runway_hours"],
            mode="lines+markers",
            name=resource,
        )
    )

threshold = positions[0]["warning_threshold_hours"]
figure.add_hline(
    y=threshold,
    line_dash="dash",
    line_color="red",
    annotation_text="Warning threshold",
)
figure.update_layout(
    title="Estimated runway over time by provider",
    xaxis_title="Hours from now",
    yaxis_title="Remaining runway (hours)",
    height=420,
)
st.plotly_chart(figure, use_container_width=True)

st.caption(
    "Runway is estimated from recent net outflow. It is not a guarantee "
    "and should be reviewed alongside freshness and operational context."
)
