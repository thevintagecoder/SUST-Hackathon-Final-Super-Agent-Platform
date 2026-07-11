"""Tests for the Operations dashboard API."""

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
)
from backend.app.routers.dashboards import (
    router as dashboards_router,
)
from synthetic_data.generator import (
    generate_bundle,
)


def create_test_alert(
    *,
    agent: Agent,
    provider: Provider,
    key: str,
    severity: str,
    status: str,
    assigned_to: str | None = None,
    human_review_required: bool = True,
) -> Alert:
    """Create one persisted operational alert."""

    return Alert(
        deduplication_key=key,
        alert_type="LIQUIDITY_RUNWAY",
        severity=severity,
        status=status,
        agent_id=agent.id,
        provider_id=provider.id,
        scenario_id="NETWORK-001",
        source_reference=key,
        title_en=(
            "Liquidity condition requires review"
        ),
        title_bn=(
            "লিকুইডিটি পরিস্থিতি "
            "পর্যালোচনা প্রয়োজন"
        ),
        title_bn_latn=(
            "Liquidity obostha review proyojon"
        ),
        message_en=(
            "The recent pattern may require review."
        ),
        message_bn=(
            "সাম্প্রতিক ধরনটি পর্যালোচনা "
            "প্রয়োজন হতে পারে।"
        ),
        message_bn_latn=(
            "Shamprotik pattern review "
            "proyojon hote pare."
        ),
        next_step_en=(
            "Verify the evidence."
        ),
        next_step_bn=(
            "প্রমাণ যাচাই করুন।"
        ),
        next_step_bn_latn=(
            "Evidence verify korun."
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
def operations_client(
    tmp_path: Path,
) -> Generator[TestClient, None, None]:
    """Create an isolated Operations dashboard."""

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

        provider = db.scalar(
            select(Provider).where(
                Provider.code
                == "NAGAD_SIM"
            )
        )

        assert len(agents) == 4
        assert provider is not None

        db.add_all(
            [
                create_test_alert(
                    agent=agents[0],
                    provider=provider,
                    key="operations-alert-1",
                    severity="HIGH",
                    status="OPEN",
                ),
                create_test_alert(
                    agent=agents[1],
                    provider=provider,
                    key="operations-alert-2",
                    severity="MEDIUM",
                    status="ACKNOWLEDGED",
                    assigned_to="ops-user",
                ),
                create_test_alert(
                    agent=agents[2],
                    provider=provider,
                    key="operations-alert-3",
                    severity="CRITICAL",
                    status="ESCALATED",
                    assigned_to="ops-manager",
                ),
                create_test_alert(
                    agent=agents[3],
                    provider=provider,
                    key="operations-alert-4",
                    severity="LOW",
                    status="RESOLVED",
                    assigned_to="ops-user",
                    human_review_required=False,
                ),
            ]
        )

        db.commit()

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


def test_operations_dashboard_summarizes_workload(
    operations_client: TestClient,
) -> None:
    """Operations should see cross-Agent workload."""

    response = operations_client.get(
        "/dashboards/operations",
        params={
            "scenario_id": "NETWORK-001",
        },
    )

    assert response.status_code == 200

    body = response.json()
    summary = body["summary"]

    assert summary["total_agents"] == 4
    assert summary["active_agents"] == 4

    assert (
        summary["active_alert_count"]
        == 3
    )

    assert summary["open_alert_count"] == 1

    assert (
        summary["escalated_alert_count"]
        == 1
    )

    assert (
        summary["unassigned_alert_count"]
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
            "human_review_required_count"
        ]
        == 3
    )

    assert (
        summary[
            "stale_provider_balance_count"
        ]
        >= 1
    )

    assert (
        summary[
            "automatic_action_taken"
        ]
        is False
    )


def test_operations_dashboard_returns_agent_risks(
    operations_client: TestClient,
) -> None:
    """Operations should receive Agent-level summaries."""

    response = operations_client.get(
        "/dashboards/operations",
        params={
            "scenario_id": "NETWORK-001",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(
        body["agent_risks"]
    ) == 4

    highest_risk_agent = (
        body["agent_risks"][0]
    )

    assert (
        highest_risk_agent[
            "highest_active_severity"
        ]
        == "CRITICAL"
    )

    assert (
        highest_risk_agent[
            "human_review_required"
        ]
        is True
    )

    assert (
        body["synthetic_data_notice"]
    )


def test_operations_dashboard_returns_multilingual_alerts(
    operations_client: TestClient,
) -> None:
    """Recent alerts should support all languages."""

    response = operations_client.get(
        "/dashboards/operations",
        params={
            "scenario_id": "NETWORK-001",
            "recent_alert_limit": 2,
        },
    )

    assert response.status_code == 200

    alerts = response.json()[
        "recent_alerts"
    ]

    assert len(alerts) == 2

    for alert in alerts:
        assert alert["title"]["en"]
        assert alert["title"]["bn"]
        assert alert["title"]["bn_latn"]

        assert (
            alert[
                "automatic_action_taken"
            ]
            is False
        )


def test_scenario_filter_excludes_other_alerts(
    operations_client: TestClient,
) -> None:
    """A different scenario should exclude alerts."""

    response = operations_client.get(
        "/dashboards/operations",
        params={
            "scenario_id": "NORMAL-001",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body[
            "summary"
        ]["active_alert_count"]
        == 0
    )

    assert body["recent_alerts"] == []