"""Agent Risk Explorer: component breakdown + EN/Bangla narrative."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from core.data_access import DataUnavailableError
from core.narrative import risk_narrative
from core.risk import assess_agent_risk
from frontend.components.filters import get_repository, render_sidebar_filters

LEVEL_COLORS = {"low": "green", "elevated": "orange", "high": "red"}

st.title("Agent Risk Explorer")
st.caption(
    "Review-priority score with a transparent component breakdown. "
    "The score prioritises human review — it is not an accusation."
)

filters = render_sidebar_filters(include_providers=False)
if filters is None:
    st.stop()

repository = get_repository()

try:
    assessment = assess_agent_risk(
        repository,
        filters.scenario.scenario_id,
        filters.agent_code,
    )
except DataUnavailableError as exc:
    st.error(str(exc))
    st.stop()

if not assessment.forecasts:
    st.info(f"No data yet for agent {filters.agent_code} in this scenario.")
    st.stop()

score_col, level_col, flag_col = st.columns(3)
score_col.metric("Review-priority score", f"{assessment.total_score:.0f}/100")
with level_col:
    st.markdown("**Level**")
    st.badge(
        assessment.level.title(),
        color=LEVEL_COLORS[assessment.level],
    )
flag_col.metric("Open flags", len(assessment.flags))

st.divider()
st.subheader("Score breakdown")

component_frame = pd.DataFrame(
    {
        "Component": [item.label for item in assessment.components],
        "Contribution": [
            round(item.weighted_score, 1) for item in assessment.components
        ],
        "Raw score": [item.score for item in assessment.components],
        "Weight": [item.weight for item in assessment.components],
    }
)
figure = px.bar(
    component_frame,
    x="Contribution",
    y="Component",
    orientation="h",
    title="Weighted contribution of each component (points of 100)",
    text="Contribution",
    hover_data=["Raw score", "Weight"],
)
figure.update_traces(textposition="outside")
figure.update_layout(
    height=320,
    yaxis={"categoryorder": "total ascending"},
)
st.plotly_chart(figure, use_container_width=True)

for component in assessment.components:
    st.markdown(
        f"**{component.label}** — {component.score:.0f}/100 raw × "
        f"{component.weight:.0%} weight"
    )
    st.caption(component.detail)

st.divider()
st.subheader("Narrative")

language_label = st.radio(
    "Language",
    options=["English", "বাংলা"],
    horizontal=True,
    key="risk_language",
)
language = "bn" if language_label == "বাংলা" else "en"
st.info(risk_narrative(assessment, language))

if assessment.flags:
    st.caption(
        "See the Anomaly Alerts page for the evidence behind each flag, "
        "and Admin Case Management to record the review outcome."
    )
