"""Shared sidebar filters (scenario, agent, provider, time window).

Selections are stored in st.session_state so every page shows the same
filter state. Pages call render_sidebar_filters() and receive one
FilterState back.
"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from core.data_access import DataUnavailableError, DemoDataRepository, ScenarioInfo


@dataclass
class FilterState:
    """Current sidebar filter selections."""

    scenario: ScenarioInfo
    agent_code: str
    provider_codes: list[str]
    horizon_hours: int


@st.cache_resource
def get_repository() -> DemoDataRepository:
    """Return one shared synthetic-data repository per session."""

    return DemoDataRepository()


def render_sidebar_filters(
    include_providers: bool = True,
    include_horizon: bool = False,
) -> FilterState | None:
    """Render shared filters in the sidebar and return the selection.

    Returns None (after rendering an explanatory message) when the
    synthetic dataset is unavailable, so pages can stop cleanly.
    """

    repository = get_repository()

    with st.sidebar:
        st.subheader("Filters")
        try:
            scenarios = repository.list_scenarios()
        except DataUnavailableError as exc:
            st.error(str(exc))
            return None

        scenario_labels = {
            scenario.scenario_id: scenario.name for scenario in scenarios
        }
        scenario_id = st.selectbox(
            "Scenario",
            options=list(scenario_labels),
            format_func=lambda key: scenario_labels[key],
            key="filter_scenario",
        )
        scenario = next(
            item for item in scenarios if item.scenario_id == scenario_id
        )
        st.caption(scenario.description)

        agents = repository.list_agents(scenario_id)
        if not agents:
            st.warning(
                f"No agents have data in scenario '{scenario.name}' yet."
            )
            return None
        agent_code = st.selectbox(
            "Agent",
            options=agents,
            key="filter_agent",
        )

        provider_codes = repository.list_providers()
        if include_providers:
            selected_providers = st.multiselect(
                "Providers",
                options=provider_codes,
                default=provider_codes,
                key="filter_providers",
            )
        else:
            selected_providers = provider_codes

        horizon_hours = 12
        if include_horizon:
            horizon_hours = st.slider(
                "Forecast horizon (hours)",
                min_value=4,
                max_value=24,
                value=12,
                key="filter_horizon",
            )

    return FilterState(
        scenario=scenario,
        agent_code=agent_code,
        provider_codes=selected_providers,
        horizon_hours=horizon_hours,
    )
