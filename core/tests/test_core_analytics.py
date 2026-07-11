"""Tests for the shared core analytics against the demo dataset."""

from __future__ import annotations

import math

import pytest

from core.anomaly import detect_anomalies
from core.data_access import DataUnavailableError, DemoDataRepository
from core.forecast import forecast_provider, forecast_scenario
from core.narrative import forecast_narrative, risk_narrative
from core.risk import assess_agent_risk

AGENT = "AGENT-SYL-001"


@pytest.fixture(scope="module")
def repository() -> DemoDataRepository:
    return DemoDataRepository()


def test_repository_lists_scenarios_and_agents(
    repository: DemoDataRepository,
) -> None:
    scenarios = repository.list_scenarios()
    scenario_ids = {scenario.scenario_id for scenario in scenarios}

    assert {
        "NORMAL-001",
        "SHORTAGE-001",
        "REPEATED-001",
        "STALE-001",
    } <= scenario_ids
    assert repository.list_agents("NORMAL-001") == [AGENT]
    assert repository.list_providers() == [
        "BKASH_SIM",
        "NAGAD_SIM",
        "ROCKET_SIM",
    ]


def test_repository_missing_directory_raises() -> None:
    from pathlib import Path

    broken = DemoDataRepository(data_dir=Path("does/not/exist"))
    with pytest.raises(DataUnavailableError):
        _ = broken.transactions


def test_forecast_detects_shortage_pressure(
    repository: DemoDataRepository,
) -> None:
    forecast = forecast_provider(
        repository,
        "SHORTAGE-001",
        AGENT,
        "BKASH_SIM",
    )

    assert forecast.net_outflow_per_hour > 0
    assert math.isfinite(forecast.runway_hours)
    assert forecast.projected_low_time is not None
    assert forecast.sample_size > 0
    assert 0 < forecast.confidence <= 0.95
    assert {"history", "forecast"} == set(forecast.timeline["kind"].unique())


def test_forecast_scenario_covers_all_providers(
    repository: DemoDataRepository,
) -> None:
    forecasts = forecast_scenario(repository, "NORMAL-001", AGENT)

    assert [item.provider_code for item in forecasts] == [
        "BKASH_SIM",
        "NAGAD_SIM",
        "ROCKET_SIM",
    ]


def test_delayed_feed_reduces_confidence(
    repository: DemoDataRepository,
) -> None:
    stale = forecast_provider(repository, "STALE-001", AGENT, "ROCKET_SIM")

    assert stale.freshness == "delayed"

    fresh_confidences = [
        forecast_provider(
            repository, "STALE-001", AGENT, provider
        ).confidence
        for provider in ("BKASH_SIM", "NAGAD_SIM")
    ]
    assert stale.confidence < min(fresh_confidences)


def test_repeated_amounts_flagged_with_evidence(
    repository: DemoDataRepository,
) -> None:
    flags = detect_anomalies(repository, "REPEATED-001", AGENT)

    repeated = [
        flag for flag in flags if flag.category == "repeated_amounts"
    ]
    assert repeated, "expected a repeated-amounts flag in REPEATED-001"

    flag = repeated[0]
    assert flag.provider_code == "BKASH_SIM"
    assert flag.metrics["repeat_count"] >= 4
    assert not flag.evidence.empty
    assert 0 < flag.confidence <= 1
    assert flag.recommended_next_step
    # The injected ground-truth transactions must be inside the evidence.
    assert flag.evidence["anomaly_expected"].any()


def test_normal_scenario_has_no_repeated_amount_flags(
    repository: DemoDataRepository,
) -> None:
    flags = detect_anomalies(repository, "NORMAL-001", AGENT)

    assert not [
        flag for flag in flags if flag.category == "repeated_amounts"
    ]


def test_risk_score_ranks_scenarios_sensibly(
    repository: DemoDataRepository,
) -> None:
    normal = assess_agent_risk(repository, "NORMAL-001", AGENT)
    repeated = assess_agent_risk(repository, "REPEATED-001", AGENT)

    assert 0 <= normal.total_score <= 100
    assert repeated.total_score > normal.total_score
    assert len(repeated.components) == 4
    assert repeated.level in {"low", "elevated", "high"}

    weights = sum(component.weight for component in repeated.components)
    assert weights == pytest.approx(1.0)


def test_narratives_in_both_languages(
    repository: DemoDataRepository,
) -> None:
    forecast = forecast_provider(
        repository,
        "SHORTAGE-001",
        AGENT,
        "BKASH_SIM",
    )
    assessment = assess_agent_risk(repository, "REPEATED-001", AGENT)

    english_forecast = forecast_narrative(forecast, "en")
    bangla_forecast = forecast_narrative(forecast, "bn")
    english_risk = risk_narrative(assessment, "en")
    bangla_risk = risk_narrative(assessment, "bn")

    assert "may run low" in english_forecast
    assert "confidence" in english_forecast
    assert bangla_forecast != english_forecast
    assert "review" in english_risk.lower()
    assert "fraud" not in english_risk.lower()
    assert bangla_risk != english_risk

    with pytest.raises(ValueError):
        forecast_narrative(forecast, "fr")
