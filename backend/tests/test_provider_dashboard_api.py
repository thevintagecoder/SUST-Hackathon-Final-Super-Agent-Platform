"""Tests for the Provider dashboard API."""

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


def create_provider_alert(
    *,
    agent: Agent,
    provider: Provider,
    key: str,
    severity: str,
    status: str,
    assigned_to: str | None = None,
    human_review_required: bool = True,
) -> Alert:
    """Create one provider-scoped test alert."""

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
            "Provider float requires review"
        ),
        title_bn=(
            "প্রোভাইডার ফ্লোট "
            "পর্যালোচনা প্রয়োজন"
        ),
        title_bn_latn=(
            "Provider float review proyojon"
        ),
        message_en=(
            "The provider balance may require review."
        ),
        message_bn=(
            "প্রোভাইডার ব্যালেন্স "
            "পর্যালোচনা প্রয়োজন হতে পারে।"
        ),
        message_bn_latn=(
            "Provider balance review "
            "proyojon hote pare."
        ),
        next_step_en=(
            "Verify the provider balance."
        ),
        next_step_bn=(
            "প্রোভাইডার ব্যালেন্স যাচাই করুন।"
        ),
        next_step_bn_latn=(
            "Provider balance verify korun."
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
def provider_client(
    tmp_path: Path,
) -> Generator[TestClient, None, None]:
    """Create an isolated Provider dashboard client."""

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

        nagad = db.scalar(
            select(Provider).where(
                Provider.code
                == "NAGAD_SIM"
            )
        )

        bkash = db.scalar(
            select(Provider).where(
                Provider.code
                == "BKASH_SIM"
            )
        )

        assert len(agents) == 4
        assert nagad is not None
        assert bkash is not None

        db.add_all(
            [
                create_provider_alert(
                    agent=agents[0],
                    provider=nagad,
                    key="provider-alert-1",
                    severity="HIGH",
                    status="OPEN",
                ),
                create_provider_alert(
                    agent=agents[1],
                    provider=nagad,
                    key="provider-alert-2",
                    severity="MEDIUM",
                    status="ACKNOWLEDGED",
                    assigned_to="provider-ops",
                ),
                create_provider_alert(
                    agent=agents[2],
                    provider=nagad,
                    key="provider-alert-3",
                    severity="CRITICAL",
                    status="ESCALATED",
                    assigned_to="provider-manager",
                ),
                create_provider_alert(
                    agent=agents[3],
                    provider=nagad,
                    key="provider-alert-4",
                    severity="LOW",
                    status="RESOLVED",
                    assigned_to="provider-ops",
                    human_review_required=False,
                ),
                create_provider_alert(
                    agent=agents[0],
                    provider=bkash,
                    key="other-provider-alert",
                    severity="HIGH",
                    status="OPEN",
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


def test_provider_dashboard_summarizes_nagad_balances(
    provider_client: TestClient,
) -> None:
    """The dashboard should summarize one provider."""

    response = provider_client.get(
        "/dashboards/providers/NAGAD_SIM",
        params={
            "scenario_id": "NETWORK-001",
        },
    )

    assert response.status_code == 200

    body = response.json()
    summary = body["summary"]

    assert (
        body["provider"]["code"]
        == "NAGAD_SIM"
    )

    assert (
        summary["agents_with_balance"]
        == 4
    )

    assert (
        Decimal(
            summary[
                "total_electronic_balance"
            ]
        )
        == Decimal("320000.00")
    )

    assert (
        Decimal(
            summary[
                "prototype_safety_threshold"
            ]
        )
        == Decimal("40000.00")
    )

    assert (
        summary[
            "at_or_below_safety_threshold_count"
        ]
        == 2
    )

    assert (
        summary["fresh_balance_count"]
        == 3
    )

    assert (
        summary[
            "non_fresh_balance_count"
        ]
        == 1
    )


def test_provider_dashboard_summarizes_alerts(
    provider_client: TestClient,
) -> None:
    """Resolved and other-provider alerts should be excluded."""

    response = provider_client.get(
        "/dashboards/providers/NAGAD_SIM",
        params={
            "scenario_id": "NETWORK-001",
        },
    )

    assert response.status_code == 200

    summary = response.json()[
        "summary"
    ]

    assert (
        summary["active_alert_count"]
        == 3
    )

    assert (
        summary["open_alert_count"]
        == 1
    )

    assert (
        summary[
            "escalated_alert_count"
        ]
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
            "automatic_action_taken"
        ]
        is False
    )


def test_provider_dashboard_prioritizes_high_risk_agents(
    provider_client: TestClient,
) -> None:
    """Critical provider risk should appear first."""

    response = provider_client.get(
        "/dashboards/providers/NAGAD_SIM",
        params={
            "scenario_id": "NETWORK-001",
        },
    )

    assert response.status_code == 200

    balances = response.json()[
        "agent_balances"
    ]

    assert len(balances) == 4

    assert (
        balances[0][
            "highest_active_severity"
        ]
        == "CRITICAL"
    )

    assert (
        balances[0][
            "human_review_required"
        ]
        is True
    )


def test_provider_dashboard_returns_multilingual_alerts(
    provider_client: TestClient,
) -> None:
    """Provider alerts should contain all title languages."""

    response = provider_client.get(
        "/dashboards/providers/NAGAD_SIM",
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


def test_unknown_provider_returns_404(
    provider_client: TestClient,
) -> None:
    """Unknown providers should return a clear 404."""

    response = provider_client.get(
        "/dashboards/providers/UNKNOWN"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Provider 'UNKNOWN' was not found."
        )
    }