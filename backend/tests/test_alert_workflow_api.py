"""Tests for the human-review alert workflow."""

from collections.abc import Generator
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
from backend.app.routers.alerts import (
    router as alerts_router,
)
from synthetic_data.generator import (
    generate_bundle,
)


@pytest.fixture
def workflow_client(
    tmp_path: Path,
) -> Generator[TestClient, None, None]:
    """Create an isolated alert workflow client."""

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
            input_directory=generated_directory,
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


def create_alert(
    client: TestClient,
) -> int:
    """Create a deterministic liquidity alert."""

    response = client.post(
        "/alerts/generate",
        json={
            "alert_type": "LIQUIDITY_RUNWAY",
            "agent_code": "AGENT-SYL-001",
            "provider_code": "NAGAD_SIM",
            "scenario_id": "FORECAST-001",
            "lookback_hours": 6,
            "warning_threshold_hours": 8,
        },
    )

    assert response.status_code == 200

    alert_id = response.json()[
        "alert_id"
    ]

    assert alert_id is not None

    return int(
        alert_id
    )


def test_alert_can_be_acknowledged(
    workflow_client: TestClient,
) -> None:
    """An OPEN alert should become ACKNOWLEDGED."""

    alert_id = create_alert(
        workflow_client
    )

    response = workflow_client.post(
        f"/alerts/{alert_id}/acknowledge",
        json={
            "actor": "ops-user-1",
            "note": "Alert reviewed.",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ACKNOWLEDGED"
    assert body["acknowledged_at"] is not None

    assert (
        body["event"]["event_type"]
        == "ACKNOWLEDGED"
    )

    assert (
        body["event"]["actor"]
        == "ops-user-1"
    )


def test_alert_can_be_assigned(
    workflow_client: TestClient,
) -> None:
    """An alert should be assigned to a human owner."""

    alert_id = create_alert(
        workflow_client
    )

    response = workflow_client.post(
        f"/alerts/{alert_id}/assign",
        json={
            "actor": "ops-lead",
            "assigned_to": "liquidity-team",
            "note": "Please verify Nagad float.",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ASSIGNED"

    assert (
        body["assigned_to"]
        == "liquidity-team"
    )

    assert (
        body["event"]["event_type"]
        == "ASSIGNED"
    )


def test_note_does_not_change_status(
    workflow_client: TestClient,
) -> None:
    """A timeline note should preserve the status."""

    alert_id = create_alert(
        workflow_client
    )

    response = workflow_client.post(
        f"/alerts/{alert_id}/notes",
        json={
            "actor": "field-coordinator",
            "note": (
                "Agent reported higher demand "
                "during a local event."
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "OPEN"

    assert (
        body["event"]["event_type"]
        == "NOTE_ADDED"
    )


def test_alert_can_be_escalated_and_resolved(
    workflow_client: TestClient,
) -> None:
    """An alert should complete the review workflow."""

    alert_id = create_alert(
        workflow_client
    )

    escalate_response = workflow_client.post(
        f"/alerts/{alert_id}/escalate",
        json={
            "actor": "ops-lead",
            "note": "Provider coordination required.",
        },
    )

    assert escalate_response.status_code == 200

    assert (
        escalate_response.json()["status"]
        == "ESCALATED"
    )

    resolve_response = workflow_client.post(
        f"/alerts/{alert_id}/resolve",
        json={
            "actor": "ops-manager",
            "note": (
                "Balance was replenished after "
                "human confirmation."
            ),
        },
    )

    assert resolve_response.status_code == 200

    body = resolve_response.json()

    assert body["status"] == "RESOLVED"
    assert body["resolved_at"] is not None

    assert (
        body["human_review_required"]
        is False
    )

    assert (
        body["automatic_action_taken"]
        is False
    )

    assert (
        body["event"]["event_type"]
        == "RESOLVED"
    )


def test_detail_contains_complete_timeline(
    workflow_client: TestClient,
) -> None:
    """The detail endpoint should preserve action history."""

    alert_id = create_alert(
        workflow_client
    )

    workflow_client.post(
        f"/alerts/{alert_id}/acknowledge",
        json={
            "actor": "ops-user",
        },
    )

    workflow_client.post(
        f"/alerts/{alert_id}/assign",
        json={
            "actor": "ops-lead",
            "assigned_to": "risk-team",
        },
    )

    workflow_client.post(
        f"/alerts/{alert_id}/notes",
        json={
            "actor": "risk-team",
            "note": "Review in progress.",
        },
    )

    detail_response = workflow_client.get(
        f"/alerts/{alert_id}"
    )

    assert detail_response.status_code == 200

    event_types = [
        event["event_type"]
        for event in detail_response.json()[
            "events"
        ]
    ]

    assert event_types == [
        "CREATED",
        "ACKNOWLEDGED",
        "ASSIGNED",
        "NOTE_ADDED",
    ]


def test_resolved_alert_cannot_be_acknowledged(
    workflow_client: TestClient,
) -> None:
    """Resolved alerts should reject invalid transitions."""

    alert_id = create_alert(
        workflow_client
    )

    resolve_response = workflow_client.post(
        f"/alerts/{alert_id}/resolve",
        json={
            "actor": "ops-manager",
            "note": "Reviewed and closed.",
        },
    )

    assert resolve_response.status_code == 200

    response = workflow_client.post(
        f"/alerts/{alert_id}/acknowledge",
        json={
            "actor": "ops-user",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Cannot acknowledge a resolved alert."
        )
    }