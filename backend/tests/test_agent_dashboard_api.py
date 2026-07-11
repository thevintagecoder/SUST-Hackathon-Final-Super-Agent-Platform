"""Tests for the Agent intelligence dashboard API."""

from collections.abc import Generator
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.data_loading.synthetic_loader import (
    load_synthetic_scenario,
)
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.routers.dashboards import (
    router as dashboards_router,
)
from backend.app.schemas.alert import (
    AlertGenerationRequest,
)
from backend.app.services.alert_generation_service import (
    generate_persisted_alert,
)
from synthetic_data.generator import (
    generate_bundle,
)


@pytest.fixture
def dashboard_client(
    tmp_path: Path,
) -> Generator[TestClient, None, None]:
    """Create an isolated Agent dashboard client."""

    generated_directory = (
        tmp_path / "generated"
    )

    generate_bundle(
        output_directory=generated_directory,
        seed=42,
    )

    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(
        engine
    )

    with Session(engine) as db:
        load_synthetic_scenario(
            db=db,
            input_directory=(
                generated_directory
            ),
            scenario_id="FORECAST-001",
        )

        result = generate_persisted_alert(
            db=db,
            request=AlertGenerationRequest(
                alert_type=(
                    "LIQUIDITY_RUNWAY"
                ),
                agent_code=(
                    "AGENT-SYL-001"
                ),
                provider_code="NAGAD_SIM",
                scenario_id="FORECAST-001",
                lookback_hours=6,
                warning_threshold_hours=(
                    Decimal("8.00")
                ),
            ),
        )

        assert result.alert_created is True

    application = FastAPI()

    application.include_router(
        dashboards_router
    )

    def override_get_db():
        with Session(engine) as db:
            yield db

    application.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(
        application
    ) as client:
        yield client

    application.dependency_overrides.clear()
    engine.dispose()


def test_agent_dashboard_combines_liquidity_and_alerts(
    dashboard_client: TestClient,
) -> None:
    """The dashboard should combine balances and risk state."""

    response = dashboard_client.get(
        "/dashboards/agents/AGENT-SYL-001",
        params={
            "scenario_id": "FORECAST-001",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["agent"]["code"]
        == "AGENT-SYL-001"
    )

    assert body["agent"]["is_active"] is True

    assert body["shared_cash"]["available"] is True

    assert (
        Decimal(
            body["shared_cash"]["balance"]
        )
        == Decimal("90000.00")
    )

    provider_balances = {
        item["provider_code"]: item
        for item in body[
            "provider_balances"
        ]
    }

    assert "NAGAD_SIM" in provider_balances

    assert (
        Decimal(
            provider_balances[
                "NAGAD_SIM"
            ]["electronic_balance"]
        )
        == Decimal("100000.00")
    )

    assert (
        provider_balances[
            "NAGAD_SIM"
        ]["freshness_state"]
        == "fresh"
    )

    assert (
        body[
            "risk_summary"
        ]["active_alert_count"]
        == 1
    )

    assert (
        body[
            "risk_summary"
        ]["highest_active_severity"]
        == "HIGH"
    )

    assert (
        body[
            "risk_summary"
        ]["human_review_required"]
        is True
    )

    assert (
        body[
            "risk_summary"
        ]["automatic_action_taken"]
        is False
    )

    assert len(
        body["recent_alerts"]
    ) == 1

    alert = body["recent_alerts"][0]

    assert (
        alert["alert_type"]
        == "LIQUIDITY_RUNWAY"
    )

    assert alert["title"]["en"]
    assert alert["title"]["bn"]
    assert alert["title"]["bn_latn"]


def test_scenario_filter_excludes_other_alerts(
    dashboard_client: TestClient,
) -> None:
    """The dashboard should respect the scenario filter."""

    response = dashboard_client.get(
        "/dashboards/agents/AGENT-SYL-001",
        params={
            "scenario_id": "NORMAL-001",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body[
            "risk_summary"
        ]["active_alert_count"]
        == 0
    )

    assert (
        body[
            "risk_summary"
        ]["highest_active_severity"]
        is None
    )

    assert body["recent_alerts"] == []


def test_unknown_agent_dashboard_returns_404(
    dashboard_client: TestClient,
) -> None:
    """Unknown Agents should return a clear 404."""

    response = dashboard_client.get(
        "/dashboards/agents/UNKNOWN-AGENT"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Agent 'UNKNOWN-AGENT' "
            "was not found."
        )
    }