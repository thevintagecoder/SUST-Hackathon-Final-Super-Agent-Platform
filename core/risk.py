"""Composite agent risk scoring with a transparent component breakdown.

The score is decision support for prioritising human review — it never
labels an agent as fraudulent. Each component is 0–100 and the total is
a weighted sum, so the dashboard can always show *why* a score is what
it is.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from core.anomaly import AnomalyFlag, detect_anomalies
from core.data_access import DemoDataRepository
from core.forecast import ProviderForecast, forecast_scenario

COMPONENT_WEIGHTS = {
    "liquidity_pressure": 0.40,
    "unusual_activity": 0.35,
    "data_freshness": 0.15,
    "flow_volatility": 0.10,
}

SEVERITY_POINTS = {"high": 55.0, "medium": 30.0, "low": 15.0}
FRESHNESS_POINTS = {"fresh": 0.0, "delayed": 60.0, "stale": 90.0}


@dataclass
class RiskComponent:
    """One scored dimension of agent risk."""

    key: str
    label: str
    score: float  # 0-100 within this component
    weight: float
    detail: str

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class RiskAssessment:
    """Composite risk assessment for one agent in one scenario."""

    agent_code: str
    scenario_id: str
    total_score: float  # 0-100
    level: str  # "low" | "elevated" | "high"
    components: list[RiskComponent]
    forecasts: list[ProviderForecast] = field(repr=False)
    flags: list[AnomalyFlag] = field(repr=False)


def _liquidity_component(forecasts: list[ProviderForecast]) -> RiskComponent:
    worst_score = 0.0
    detail = "All provider floats have comfortable runway."
    for forecast in forecasts:
        if not math.isfinite(forecast.runway_hours):
            continue
        threshold = forecast.warning_threshold_hours
        # Runway at or below the threshold scales from 60 to 100;
        # above the threshold it decays toward 0 by 4x threshold.
        if forecast.runway_hours <= threshold:
            score = 60.0 + 40.0 * (1.0 - forecast.runway_hours / threshold)
        else:
            score = max(
                0.0,
                60.0 * (1.0 - (forecast.runway_hours - threshold) / (3 * threshold)),
            )
        if score > worst_score:
            worst_score = score
            detail = (
                f"{forecast.provider_code} runway is about "
                f"{forecast.runway_hours:.1f} hours (warning threshold "
                f"{threshold:.0f} hours)."
            )
    return RiskComponent(
        key="liquidity_pressure",
        label="Liquidity pressure",
        score=round(worst_score, 1),
        weight=COMPONENT_WEIGHTS["liquidity_pressure"],
        detail=detail,
    )


def _unusual_activity_component(flags: list[AnomalyFlag]) -> RiskComponent:
    if not flags:
        return RiskComponent(
            key="unusual_activity",
            label="Unusual activity",
            score=0.0,
            weight=COMPONENT_WEIGHTS["unusual_activity"],
            detail="No unusual-activity flags in this scenario window.",
        )
    score = 0.0
    for flag in flags:
        score += SEVERITY_POINTS[flag.severity] * flag.confidence
    score = min(100.0, score)
    detail = (
        f"{len(flags)} open flag(s); most severe: {flags[0].title}"
    )
    return RiskComponent(
        key="unusual_activity",
        label="Unusual activity",
        score=round(score, 1),
        weight=COMPONENT_WEIGHTS["unusual_activity"],
        detail=detail,
    )


def _freshness_component(forecasts: list[ProviderForecast]) -> RiskComponent:
    worst = max(
        (FRESHNESS_POINTS.get(forecast.freshness, 30.0) for forecast in forecasts),
        default=0.0,
    )
    degraded = [
        forecast.provider_code
        for forecast in forecasts
        if forecast.freshness != "fresh"
    ]
    detail = (
        "All provider feeds are fresh."
        if not degraded
        else f"Degraded feeds: {', '.join(degraded)} — estimates for these "
        "providers are provisional."
    )
    return RiskComponent(
        key="data_freshness",
        label="Data freshness",
        score=round(worst, 1),
        weight=COMPONENT_WEIGHTS["data_freshness"],
        detail=detail,
    )


def _volatility_component(forecasts: list[ProviderForecast]) -> RiskComponent:
    worst = max((forecast.volatility for forecast in forecasts), default=0.0)
    score = min(100.0, worst * 50.0)
    detail = (
        f"Highest hourly net-flow volatility across providers: {worst:.2f}."
    )
    return RiskComponent(
        key="flow_volatility",
        label="Flow volatility",
        score=round(score, 1),
        weight=COMPONENT_WEIGHTS["flow_volatility"],
        detail=detail,
    )


def _level_for_score(total: float) -> str:
    if total >= 60:
        return "high"
    if total >= 30:
        return "elevated"
    return "low"


def assess_agent_risk(
    repository: DemoDataRepository,
    scenario_id: str,
    agent_code: str,
) -> RiskAssessment:
    """Compute the composite risk assessment for one agent."""

    forecasts = forecast_scenario(repository, scenario_id, agent_code)
    flags = detect_anomalies(repository, scenario_id, agent_code)

    components = [
        _liquidity_component(forecasts),
        _unusual_activity_component(flags),
        _freshness_component(forecasts),
        _volatility_component(forecasts),
    ]
    total = round(sum(component.weighted_score for component in components), 1)

    return RiskAssessment(
        agent_code=agent_code,
        scenario_id=scenario_id,
        total_score=total,
        level=_level_for_score(total),
        components=components,
        forecasts=forecasts,
        flags=flags,
    )
