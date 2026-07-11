"""Tests for the Management dashboard API."""

from collections.abc import Generator
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import (
    create_engine,
    select,
)
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.data_loading.synthetic_loader import (
    load_synthetic_scenario,
)
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.models import (
    Agent,
    Alert,
    Provider,
    SupportRequest,
)
from backend.app.routers.dashboards import (
    router as dashboards_router,
)
from synthetic_data.generator import (
    generate_bundle,
)


def create_management_alert(
    *,
    agent: Agent,
    provider: Provider,
    key: str,
    severity: str,
    status: str,
    assigned_to: str | None = None,
    human_review_required: bool = True,
) -> Alert:
    """Create one management dashboard test alert."""

    return Alert(
        deduplication_key=key,
        alert_type="LIQUIDITY_RUNWAY",
        severity=severity,
        status=status,
        agent_id=agent.id,
        provider_id=provider.id,
        scenario_id="NETWORK-001",
        source_reference=key,
        title_en="Liquidity review required",
        title_bn=(
            "লিকুইডিটি পর্যালোচনা প্রয়োজন"
        ),
        title_bn_latn=(
            "Liquidity review proyojon"
        ),
        message_en=(
            "The liquidity condition requires review."
        ),
        message_bn=(
            "লিকুইডিটি পরিস্থিতি "
            "পর্যালোচনা প্রয়োজন।"
        ),
        message_bn_latn=(
            "Liquidity obostha review proyojon."
        ),
        next_step_en=(
            "Verify the available evidence."
        ),
        next_step_bn=(
            "উপলব্ধ প্রমাণ যাচাই করুন।"
        ),
        next_step_bn_latn=(
            "Available evidence verify korun."
        ),
        evidence={
            "synthetic": True,
        },
        confidence=Decimal(
            "0.8000"
        ),
        freshness_state="fresh",
        assigned_to=assigned_to,
        human_review_required=(
            human_review_required
        ),
        automatic_action_taken=False,
    )


@pytest.fixture
def management_client(
    tmp_path: Path,
) -> Generator[
    tuple[TestClient, dict[str, int]],
    None,
    None,
]:
    """Create an isolated Management dashboard."""

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
            scenario_id="NETWORK-001",
        )

        agents = list(
            db.scalars(
                select(Agent).order_by(
                    Agent.code
                )
            ).all()
        )

        providers = list(
            db.scalars(
                select(Provider).order_by(
                    Provider.code
                )
            ).all()
        )

        assert agents
        assert providers

        db.add_all(
            [
                create_management_alert(
                    agent=agents[0],
                    provider=providers[0],
                    key="management-alert-1",
                    severity="HIGH",
                    status="OPEN",
                ),
                create_management_alert(
                    agent=agents[1],
                    provider=providers[0],
                    key="management-alert-2",
                    severity="CRITICAL",
                    status="ESCALATED",
                    assigned_to="management-user",
                ),
                create_management_alert(
                    agent=agents[2],
                    provider=providers[1],
                    key="management-alert-3",
                    severity="MEDIUM",
                    status="RESOLVED",
                    assigned_to="operations-user",
                    human_review_required=False,
                ),
            ]
        )

        db.commit()

        expected = {
            "agents": len(
                db.scalars(
                    select(Agent)
                ).all()
            ),
            "providers": len(
                db.scalars(
                    select(Provider)
                ).all()
            ),
            "support_requests": len(
                db.scalars(
                    select(SupportRequest)
                ).all()
            ),
        }

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
        yield client, expected

    application.dependency_overrides.clear()
    engine.dispose()


def test_management_dashboard_returns_network_kpis(
    management_client: tuple[
        TestClient,
        dict[str, int],
    ],
) -> None:
    """Management should receive network-wide KPIs."""

    client, expected = management_client

    response = client.get(
        "/dashboards/management",
        params={
            "scenario_id": "NETWORK-001",
        },
    )

    assert response.status_code == 200

    body = response.json()
    summary = body["summary"]

    assert (
        summary["total_agents"]
        == expected["agents"]
    )

    assert (
        summary["total_providers"]
        == expected["providers"]
    )

    assert (
        summary["support_request_count"]
        == expected["support_requests"]
    )

    assert (
        summary["active_alert_count"]
        == 2
    )

    assert (
        summary["resolved_alert_count"]
        == 1
    )

    assert (
        summary["escalated_alert_count"]
        == 1
    )

    assert (
        summary[
            "high_or_critical_alert_count"
        ]
        == 2
    )

    assert (
        summary[
            "automatic_action_taken"
        ]
        is False
    )


def test_management_dashboard_returns_provider_risks(
    management_client: tuple[
        TestClient,
        dict[str, int],
    ],
) -> None:
    """Provider risk rows should be available."""

    client, _ = management_client

    response = client.get(
        "/dashboards/management",
        params={
            "scenario_id": "NETWORK-001",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["provider_risks"]

    first_provider = body[
        "provider_risks"
    ][0]

    assert (
        first_provider[
            "highest_active_severity"
        ]
        == "CRITICAL"
    )

    assert (
        first_provider[
            "human_review_required"
        ]
        is True
    )


def test_management_dashboard_returns_workflow_counts(
    management_client: tuple[
        TestClient,
        dict[str, int],
    ],
) -> None:
    """Management should see workflow status counts."""

    client, _ = management_client

    response = client.get(
        "/dashboards/management",
        params={
            "scenario_id": "NETWORK-001",
        },
    )

    assert response.status_code == 200

    summary = response.json()[
        "summary"
    ]

    assert (
        summary["alert_status_counts"][
            "OPEN"
        ]
        == 1
    )

    assert (
        summary["alert_status_counts"][
            "ESCALATED"
        ]
        == 1
    )

    assert (
        summary["alert_status_counts"][
            "RESOLVED"
        ]
        == 1
    )

    assert isinstance(
        summary[
            "support_request_status_counts"
        ],
        dict,
    )


def test_management_dashboard_includes_safety_notices(
    management_client: tuple[
        TestClient,
        dict[str, int],
    ],
) -> None:
    """Management should see synthetic-data warnings."""

    client, _ = management_client

    response = client.get(
        "/dashboards/management"
    )

    assert response.status_code == 200

    body = response.json()

    assert body[
        "synthetic_data_notice"
    ]

    assert body[
        "decision_support_notice"
    ]