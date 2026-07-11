"""Final backend evaluation and contract tests."""

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
from backend.app.main import app as main_app
from backend.app.routers.alerts import (
    router as alerts_router,
)
from backend.app.routers.dashboards import (
    router as dashboards_router,
)
from synthetic_data.generator import (
    generate_bundle,
)


@pytest.fixture
def final_backend_client(
    tmp_path: Path,
) -> Generator[TestClient, None, None]:
    """Create an isolated final integration client."""

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

    application = FastAPI(
        title="Final Backend Integration Test",
    )

    application.include_router(
        alerts_router
    )

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


def test_evaluation_dashboard_returns_expected_metrics(
    final_backend_client: TestClient,
) -> None:
    """The controlled evaluation metrics should be stable."""

    response = final_backend_client.get(
        "/dashboards/evaluation"
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["benchmark_id"]
        == "CONTROLLED-SYNTHETIC-001"
    )

    assert (
        body["dataset_type"]
        == "controlled_synthetic"
    )

    forecast = body["forecast"]

    assert (
        Decimal(
            forecast[
                "predicted_runway_hours"
            ]
        )
        == Decimal("8.00")
    )

    assert (
        Decimal(
            forecast[
                "actual_breach_hours"
            ]
        )
        == Decimal("8.50")
    )

    assert (
        Decimal(
            forecast[
                "absolute_error_hours"
            ]
        )
        == Decimal("0.50")
    )

    assert (
        Decimal(
            forecast[
                "warning_lead_time_hours"
            ]
        )
        == Decimal("8.50")
    )

    assert (
        forecast["benchmark_passed"]
        is True
    )

    anomaly = body["anomaly"]

    assert anomaly["true_positive"] == 1
    assert anomaly["true_negative"] == 1
    assert anomaly["false_positive"] == 0
    assert anomaly["false_negative"] == 0

    assert (
        Decimal(
            anomaly["precision"]
        )
        == Decimal("1.0000")
    )

    assert (
        Decimal(
            anomaly["recall"]
        )
        == Decimal("1.0000")
    )

    assert (
        Decimal(
            anomaly[
                "false_positive_rate"
            ]
        )
        == Decimal("0.0000")
    )

    assert (
        anomaly["benchmark_passed"]
        is True
    )


def test_openapi_contains_required_backend_contracts(
) -> None:
    """The real application should expose required routes."""

    schema = main_app.openapi()
    paths = schema["paths"]

    required_operations = {
        (
            "/health",
            "get",
        ),
        (
            "/liquidity/check-serviceability",
            "post",
        ),
        (
            "/network/find-support",
            "post",
        ),
        (
            "/forecasts/liquidity-runway",
            "post",
        ),
        (
            "/anomalies/detect",
            "post",
        ),
        (
            "/alerts/generate",
            "post",
        ),
        (
            "/alerts",
            "get",
        ),
        (
            "/alerts/{alert_id}",
            "get",
        ),
        (
            "/alerts/{alert_id}/acknowledge",
            "post",
        ),
        (
            "/alerts/{alert_id}/assign",
            "post",
        ),
        (
            "/alerts/{alert_id}/notes",
            "post",
        ),
        (
            "/alerts/{alert_id}/escalate",
            "post",
        ),
        (
            "/alerts/{alert_id}/resolve",
            "post",
        ),
        (
            "/dashboards/agents/{agent_code}",
            "get",
        ),
        (
            "/dashboards/operations",
            "get",
        ),
        (
            "/dashboards/providers/{provider_code}",
            "get",
        ),
        (
            "/dashboards/management",
            "get",
        ),
        (
            "/dashboards/evaluation",
            "get",
        ),
    }

    for path, method in required_operations:
        assert path in paths, (
            f"Missing OpenAPI path: {path}"
        )

        assert method in paths[path], (
            f"Missing {method.upper()} "
            f"operation for {path}"
        )


def test_openapi_operation_ids_are_unique(
) -> None:
    """Every documented operation should have a unique ID."""

    schema = main_app.openapi()

    operation_ids: list[str] = []

    for path_item in schema[
        "paths"
    ].values():
        for operation in path_item.values():
            if not isinstance(
                operation,
                dict,
            ):
                continue

            operation_id = operation.get(
                "operationId"
            )

            if operation_id is not None:
                operation_ids.append(
                    operation_id
                )

    assert len(
        operation_ids
    ) == len(
        set(
            operation_ids
        )
    )


def test_complete_alert_and_dashboard_workflow(
    final_backend_client: TestClient,
) -> None:
    """Exercise the complete reviewable alert lifecycle."""

    create_response = (
        final_backend_client.post(
            "/alerts/generate",
            json={
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
                "lookback_hours": 6,
                "warning_threshold_hours": 8,
            },
        )
    )

    assert create_response.status_code == 200

    created = create_response.json()

    assert (
        created["condition_detected"]
        is True
    )

    assert (
        created["alert_created"]
        is True
    )

    assert (
        created[
            "automatic_action_taken"
        ]
        is False
    )

    alert_id = created["alert_id"]

    assert alert_id is not None

    list_response = final_backend_client.get(
        "/alerts",
        params={
            "scenario_id": (
                "FORECAST-001"
            ),
        },
    )

    assert list_response.status_code == 200

    assert (
        list_response.json()["total"]
        == 1
    )

    acknowledge_response = (
        final_backend_client.post(
            (
                f"/alerts/{alert_id}"
                "/acknowledge"
            ),
            json={
                "actor": (
                    "final-test-reviewer"
                ),
                "note": (
                    "Controlled alert reviewed."
                ),
            },
        )
    )

    assert (
        acknowledge_response.status_code
        == 200
    )

    assert (
        acknowledge_response.json()[
            "status"
        ]
        == "ACKNOWLEDGED"
    )

    dashboard_response = (
        final_backend_client.get(
            (
                "/dashboards/agents/"
                "AGENT-SYL-001"
            ),
            params={
                "scenario_id": (
                    "FORECAST-001"
                ),
            },
        )
    )

    assert (
        dashboard_response.status_code
        == 200
    )

    dashboard = dashboard_response.json()

    assert (
        dashboard[
            "risk_summary"
        ]["active_alert_count"]
        == 1
    )

    assert (
        dashboard[
            "risk_summary"
        ]["human_review_required"]
        is True
    )

    assert (
        dashboard[
            "risk_summary"
        ]["automatic_action_taken"]
        is False
    )

    resolve_response = (
        final_backend_client.post(
            f"/alerts/{alert_id}/resolve",
            json={
                "actor": (
                    "final-test-reviewer"
                ),
                "note": (
                    "Controlled review completed."
                ),
            },
        )
    )

    assert (
        resolve_response.status_code
        == 200
    )

    resolved = resolve_response.json()

    assert (
        resolved["status"]
        == "RESOLVED"
    )

    assert (
        resolved[
            "human_review_required"
        ]
        is False
    )

    assert (
        resolved[
            "automatic_action_taken"
        ]
        is False
    )

    detail_response = (
        final_backend_client.get(
            f"/alerts/{alert_id}"
        )
    )

    assert (
        detail_response.status_code
        == 200
    )

    event_types = {
        event["event_type"]
        for event
        in detail_response.json()[
            "events"
        ]
    }

    assert {
        "CREATED",
        "ACKNOWLEDGED",
        "RESOLVED",
    }.issubset(
        event_types
    )

    final_dashboard_response = (
        final_backend_client.get(
            (
                "/dashboards/agents/"
                "AGENT-SYL-001"
            ),
            params={
                "scenario_id": (
                    "FORECAST-001"
                ),
            },
        )
    )

    assert (
        final_dashboard_response
        .status_code
        == 200
    )

    assert (
        final_dashboard_response.json()[
            "risk_summary"
        ]["active_alert_count"]
        == 0
    )