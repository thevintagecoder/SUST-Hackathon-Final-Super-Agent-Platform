"""Operations overview dashboard page."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.components.metric_cards import (
    format_currency,
    render_alert_summary,
    render_provider_card,
    render_shared_cash_card,
)
from frontend.config import get_active_data_mode, get_provider

st.title("Operations Overview")
st.caption(
    f"Shared physical cash and provider balances are tracked separately. "
    f"Data mode: **{get_active_data_mode()}**"
)

try:
    provider = get_provider()
    overview = provider.get_overview()
except Exception as exc:
    st.error(str(exc))
    st.stop()

agent = overview["agent"]
st.subheader(agent["name"])
st.write(
    f"Agent code: **{agent['code']}** · Area: **{agent['area']}** · "
    f"Last updated: **{overview['generated_at']}**"
)

render_shared_cash_card(overview["shared_cash"])

st.divider()
st.subheader("Provider electronic balances")
st.caption(
    "Each provider balance is shown separately and must not be treated "
    "as interchangeable float."
)

provider_columns = st.columns(3)
for column, provider_data in zip(
    provider_columns,
    overview["providers"],
    strict=True,
):
    with column:
        render_provider_card(provider_data)

chart_frame = pd.DataFrame(overview["providers"])
figure = px.bar(
    chart_frame,
    x="balance",
    y="code",
    orientation="h",
    title="Provider balances (separate resources)",
    labels={"balance": "Electronic balance", "code": "Provider"},
    text="balance",
)
figure.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
figure.update_layout(yaxis={"categoryorder": "total ascending"}, height=360)
st.plotly_chart(figure, use_container_width=True)

st.divider()
render_alert_summary(
    overview["open_alerts"],
    overview["unacknowledged_alerts"],
)

st.caption(
    "Shared cash total: "
    f"{format_currency(overview['shared_cash']['amount'])} — kept "
    "separate from provider electronic balances above."
)
