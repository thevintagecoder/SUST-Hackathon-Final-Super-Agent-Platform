"""Tests for persisted multilingual alert API routes."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.data_loading.synthetic_loader import (
    load_synthetic_scenario,
)
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.routers.alerts import (
    router as alerts_router,
)
from synthetic_data.generator import (
    generate_bundle,
)


@pytest.fixture
def alert_client(
    tmp_path: Path,
) -> Generator[TestClient, None, None]:
    """Create an isolated alert API client."""

    generated_directory = (
        tmp_path / "generated"
    )

    generate_bundle(
        output_directory=generated_directory,
        seed=42,
    )

    engine: Engine = create_engine(
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

    application = FastAPI()

    application.include_router(
        alerts_router
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


def forecast_alert_payload() -> dict[str, object]:
    """Return a deterministic runway alert request."""

    return {
        "alert_type": "LIQUIDITY_RUNWAY",
        "agent_code": "AGENT-SYL-001",
        "provider_code": "NAGAD_SIM",
        "scenario_id": "FORECAST-001",
        "lookback_hours": 6,
        "warning_threshold_hours": 8,
    }


def create_forecast_alert(
    client: TestClient,
) -> int:
    """Create and return one deterministic alert ID."""

    response = client.post(
        "/alerts/generate",
        json=forecast_alert_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["condition_detected"] is True
    assert body["alert_id"] is not None

    return int(
        body["alert_id"]
    )


def test_generate_endpoint_persists_alert(
    alert_client: TestClient,
) -> None:
    """The API should persist a detected alert."""

    response = alert_client.post(
        "/alerts/generate",
        json=forecast_alert_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["alert_type"] == (
        "LIQUIDITY_RUNWAY"
    )

    assert body["condition_detected"] is True
    assert body["alert_created"] is True
    assert body["deduplicated"] is False
    assert body["alert_id"] is not None

    assert (
        body["human_review_required"]
        is True
    )

    assert (
        body["automatic_action_taken"]
        is False
    )


def test_generate_endpoint_deduplicates_alert(
    alert_client: TestClient,
) -> None:
    """The same evidence should not create two alerts."""

    first_response = alert_client.post(
        "/alerts/generate",
        json=forecast_alert_payload(),
    )

    second_response = alert_client.post(
        "/alerts/generate",
        json=forecast_alert_payload(),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_body = first_response.json()
    second_body = second_response.json()

    assert first_body["alert_created"] is True

    assert (
        second_body["alert_created"]
        is False
    )

    assert (
        second_body["deduplicated"]
        is True
    )

    assert (
        second_body["alert_id"]
        == first_body["alert_id"]
    )


def test_list_endpoint_supports_filters(
    alert_client: TestClient,
) -> None:
    """Alert lists should support workflow filters."""

    alert_id = create_forecast_alert(
        alert_client
    )

    response = alert_client.get(
        "/alerts",
        params={
            "status": "OPEN",
            "alert_type": (
                "LIQUIDITY_RUNWAY"
            ),
            "agent_code": (
                "AGENT-SYL-001"
            ),
            "provider_code": (
                "NAGAD_SIM"
            ),
            "scenario_id": (
                "FORECAST-001"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert len(body["items"]) == 1

    item = body["items"][0]

    assert item["id"] == alert_id
    assert item["status"] == "OPEN"

    assert (
        item["alert_type"]
        == "LIQUIDITY_RUNWAY"
    )

    assert (
        item["agent_code"]
        == "AGENT-SYL-001"
    )

    assert (
        item["provider_code"]
        == "NAGAD_SIM"
    )

    assert item["title"]["en"]
    assert item["title"]["bn"]
    assert item["title"]["bn_latn"]


def test_detail_endpoint_returns_evidence_and_timeline(
    alert_client: TestClient,
) -> None:
    """Alert details should include all localized text."""

    alert_id = create_forecast_alert(
        alert_client
    )

    response = alert_client.get(
        f"/alerts/{alert_id}"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == alert_id

    assert body["message"]["en"]
    assert body["message"]["bn"]
    assert body["message"]["bn_latn"]

    assert body["next_step"]["en"]
    assert body["next_step"]["bn"]
    assert body["next_step"]["bn_latn"]

    assert (
        body["evidence"]["runway_hours"]
        == "8.00"
    )

    assert len(body["events"]) == 1

    assert (
        body["events"][0]["event_type"]
        == "CREATED"
    )

    assert (
        body["events"][0]["actor"]
        == "system"
    )


def test_unknown_alert_returns_404(
    alert_client: TestClient,
) -> None:
    """An unknown alert ID should return 404."""

    response = alert_client.get(
        "/alerts/999999"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Alert '999999' was not found."
        )
    }