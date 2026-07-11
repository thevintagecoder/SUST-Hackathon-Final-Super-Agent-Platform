"""Unusual activity review page with responsible language."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.components.alert_card import render_alert_card
from frontend.config import get_active_data_mode, get_provider

st.title("Anomaly Review")
st.caption(
    f"Review unusual activity evidence with safe next steps. "
    f"Data mode: **{get_active_data_mode()}**"
)

try:
    provider = get_provider()
    alerts = provider.list_alerts()
except Exception as exc:
    st.error(str(exc))
    st.stop()

if not alerts:
    st.info("No alerts are open for review.")
    st.stop()

primary_alert = alerts[0]
render_alert_card(primary_alert)

st.divider()
st.subheader("Velocity comparison")
velocity_ratio = primary_alert["evidence"].get("velocity_ratio", 1.0)
velocity_frame = pd.DataFrame(
    {
        "window": ["Baseline", "Current window"],
        "transactions_per_hour": [10, 10 * velocity_ratio],
    }
)
velocity_figure = px.bar(
    velocity_frame,
    x="window",
    y="transactions_per_hour",
    title="Transaction velocity: current window vs baseline",
    labels={"transactions_per_hour": "Transactions per hour"},
    text="transactions_per_hour",
)
velocity_figure.update_traces(texttemplate="%{y:.1f}", textposition="outside")
st.plotly_chart(velocity_figure, use_container_width=True)

st.subheader("Repeated amounts")
repeat_count = int(primary_alert["evidence"].get("repeat_count", 0))
repeated_amount = primary_alert["evidence"].get("repeated_amount", 0.0)
repeat_rows = [
    {
        "Amount": repeated_amount,
        "Occurrences": 1,
    }
    for _ in range(repeat_count)
]
repeat_frame = pd.DataFrame(repeat_rows)
if not repeat_frame.empty:
    repeat_summary = (
        repeat_frame.groupby("Amount", as_index=False)["Occurrences"]
        .count()
        .rename(columns={"Occurrences": "Frequency"})
    )
    st.dataframe(repeat_summary, hide_index=True, use_container_width=True)
else:
    st.info("No repeated amount pattern is present for this alert.")

st.subheader("Possible explanation")
st.write(
    "A local event or short-term demand increase may explain the repeated "
    "cash-in pattern. Review provider float requirements and confirm feed "
    "freshness before taking operational action."
)
st.info(primary_alert["recommended_next_step"])

st.divider()
st.subheader("All open alerts")
for alert in alerts:
    with st.expander(alert["title"], expanded=False):
        render_alert_card(alert)
