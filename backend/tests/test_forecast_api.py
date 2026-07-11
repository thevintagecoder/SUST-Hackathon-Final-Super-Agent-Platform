"""API tests for explainable liquidity runway forecasts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.models import (
    Agent,
    AgentPosition,
    Provider,
    ProviderBalance,
    Transaction,
)
from backend.app.routers.forecasts import router


FORECAST_TIME = datetime(
    2026,
    7,
    11,
    12,
    0,
    tzinfo=UTC,
)


def add_transaction(
    *,
    db,
    external_id: str,
    agent_id: int,
    provider_id: int,
    transaction_type: str,
    amount: str,
    occurred_at: datetime,
) -> None:
    """Insert one completed synthetic transaction."""

    db.add(
        Transaction(
            external_id=external_id,
            scenario_id="FORECAST-TEST",
            agent_id=agent_id,
            provider_id=provider_id,
            synthetic_customer_id=(
                f"CUSTOMER-{external_id}"
            ),
            transaction_type=transaction_type,
            amount=Decimal(amount),
            occurred_at=occurred_at,
            status="completed",
            anomaly_expected=False,
            anomaly_category=None,
            injection_start_time=None,
        )
    )


@pytest.fixture
def forecast_client():
    """Create an isolated forecast API."""

    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(engine)

    with session_factory() as db:
        primary_agent = Agent(
            code="AGENT-FORECAST-001",
            name="Synthetic Forecast Agent",
            area="Sylhet",
        )

        no_history_agent = Agent(
            code="AGENT-FORECAST-002",
            name="Synthetic No-History Agent",
            area="Sylhet",
        )

        nagad = Provider(
            code="NAGAD_SIM",
            name="Synthetic Nagad Provider",
        )

        bkash = Provider(
            code="BKASH_SIM",
            name="Synthetic Bkash Provider",
        )

        db.add_all(
            [
                primary_agent,
                no_history_agent,
                nagad,
                bkash,
            ]
        )
        db.flush()

        db.add_all(
            [
                AgentPosition(
                    agent_id=primary_agent.id,
                    shared_cash=Decimal("140000.00"),
                    as_of=FORECAST_TIME,
                ),
                AgentPosition(
                    agent_id=no_history_agent.id,
                    shared_cash=Decimal("70000.00"),
                    as_of=FORECAST_TIME,
                ),
                ProviderBalance(
                    agent_id=primary_agent.id,
                    provider_id=nagad.id,
                    electronic_balance=Decimal("100000.00"),
                    last_update_at=FORECAST_TIME,
                    freshness_state="fresh",
                ),
                ProviderBalance(
                    agent_id=primary_agent.id,
                    provider_id=bkash.id,
                    electronic_balance=Decimal("100000.00"),
                    last_update_at=FORECAST_TIME,
                    freshness_state="fresh",
                ),
                ProviderBalance(
                    agent_id=no_history_agent.id,
                    provider_id=nagad.id,
                    electronic_balance=Decimal("70000.00"),
                    last_update_at=FORECAST_TIME,
                    freshness_state="fresh",
                ),
            ]
        )

        nagad_transactions = [
            (
                "NAGAD-001",
                "cash_in",
                "10000.00",
                FORECAST_TIME - timedelta(hours=4),
            ),
            (
                "NAGAD-002",
                "cash_in",
                "10000.00",
                FORECAST_TIME
                - timedelta(hours=3, minutes=15),
            ),
            (
                "NAGAD-003",
                "cash_in",
                "10000.00",
                FORECAST_TIME
                - timedelta(hours=2, minutes=30),
            ),
            (
                "NAGAD-004",
                "cash_in",
                "10000.00",
                FORECAST_TIME
                - timedelta(hours=1, minutes=45),
            ),
            (
                "NAGAD-005",
                "cash_out",
                "5000.00",
                FORECAST_TIME - timedelta(hours=1),
            ),
            (
                "NAGAD-006",
                "cash_out",
                "5000.00",
                FORECAST_TIME,
            ),
        ]

        for (
            external_id,
            transaction_type,
            amount,
            occurred_at,
        ) in nagad_transactions:
            add_transaction(
                db=db,
                external_id=external_id,
                agent_id=primary_agent.id,
                provider_id=nagad.id,
                transaction_type=transaction_type,
                amount=amount,
                occurred_at=occurred_at,
            )

        for index in range(5):
            add_transaction(
                db=db,
                external_id=f"BKASH-{index + 1:03d}",
                agent_id=primary_agent.id,
                provider_id=bkash.id,
                transaction_type="cash_out",
                amount="30000.00",
                occurred_at=(
                    FORECAST_TIME
                    - timedelta(
                        hours=4 - index,
                    )
                ),
            )

        db.commit()

    def override_get_db():
        db = session_factory()

        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(app) as client:
        yield client, session_factory

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_provider_float_runway_is_explainable(
    forecast_client,
) -> None:
    """Forecast provider-float depletion transparently."""

    client, _ = forecast_client

    response = client.post(
        "/forecasts/liquidity-runway",
        json={
            "agent_code": "AGENT-FORECAST-001",
            "resource_type": "provider_float",
            "provider_code": "NAGAD_SIM",
            "lookback_hours": 4,
            "warning_threshold_hours": 8,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["risk_level"] == "HIGH"
    assert body["completed_transaction_count"] == 6

    assert Decimal(
        str(body["current_balance"])
    ) == Decimal("100000.00")

    assert Decimal(
        str(body["safety_threshold"])
    ) == Decimal("40000.00")

    assert Decimal(
        str(body["gross_consumption"])
    ) == Decimal("40000.00")

    assert Decimal(
        str(body["gross_replenishment"])
    ) == Decimal("10000.00")

    assert Decimal(
        str(body["net_consumption"])
    ) == Decimal("30000.00")

    assert Decimal(
        str(body["net_consumption_per_hour"])
    ) == Decimal("7500.00")

    assert Decimal(
        str(body["runway_hours"])
    ) == Decimal("8.00")

    assert body[
        "estimated_threshold_breach_time"
    ] is not None

    assert body["automatic_action_taken"] is False
    assert body["human_review_required"] is True
    assert len(body["explanation_factors"]) >= 5


def test_physical_cash_uses_all_provider_transactions(
    forecast_client,
) -> None:
    """Physical-cash forecasts should combine all providers."""

    client, _ = forecast_client

    response = client.post(
        "/forecasts/liquidity-runway",
        json={
            "agent_code": "AGENT-FORECAST-001",
            "resource_type": "physical_cash",
            "lookback_hours": 4,
            "warning_threshold_hours": 8,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["provider_code"] is None
    assert body["risk_level"] == "HIGH"

    assert Decimal(
        str(body["gross_consumption"])
    ) == Decimal("160000.00")

    assert Decimal(
        str(body["gross_replenishment"])
    ) == Decimal("40000.00")

    assert Decimal(
        str(body["net_consumption"])
    ) == Decimal("120000.00")

    assert Decimal(
        str(body["net_consumption_per_hour"])
    ) == Decimal("30000.00")

    assert Decimal(
        str(body["runway_hours"])
    ) == Decimal("3.33")


def test_replenishing_provider_has_no_breach_estimate(
    forecast_client,
) -> None:
    """A replenishing resource should not get a false breach time."""

    client, _ = forecast_client

    response = client.post(
        "/forecasts/liquidity-runway",
        json={
            "agent_code": "AGENT-FORECAST-001",
            "resource_type": "provider_float",
            "provider_code": "BKASH_SIM",
            "lookback_hours": 4,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["risk_level"]
        == "STABLE_OR_REPLENISHING"
    )
    assert body["runway_hours"] is None
    assert (
        body["estimated_threshold_breach_time"]
        is None
    )


def test_delayed_data_reduces_confidence(
    forecast_client,
) -> None:
    """Delayed balance data should lower forecast confidence."""

    client, session_factory = forecast_client

    with session_factory() as db:
        balance = db.scalar(
            select(ProviderBalance)
            .join(
                Provider,
                Provider.id
                == ProviderBalance.provider_id,
            )
            .where(
                Provider.code == "NAGAD_SIM",
                ProviderBalance.agent_id == 1,
            )
        )

        assert balance is not None

        balance.freshness_state = "delayed"
        db.commit()

    response = client.post(
        "/forecasts/liquidity-runway",
        json={
            "agent_code": "AGENT-FORECAST-001",
            "resource_type": "provider_float",
            "provider_code": "NAGAD_SIM",
            "lookback_hours": 4,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["freshness_state"] == "delayed"
    assert Decimal(
        str(body["confidence"])
    ) < Decimal("0.80")
    assert body["human_review_required"] is True


def test_provider_float_requires_provider_code(
    forecast_client,
) -> None:
    """Provider-float forecasts require a provider."""

    client, _ = forecast_client

    response = client.post(
        "/forecasts/liquidity-runway",
        json={
            "agent_code": "AGENT-FORECAST-001",
            "resource_type": "provider_float",
            "lookback_hours": 4,
        },
    )

    assert response.status_code == 400


def test_unknown_agent_returns_404(
    forecast_client,
) -> None:
    """Unknown Agents should fail clearly."""

    client, _ = forecast_client

    response = client.post(
        "/forecasts/liquidity-runway",
        json={
            "agent_code": "AGENT-UNKNOWN",
            "resource_type": "physical_cash",
            "lookback_hours": 4,
        },
    )

    assert response.status_code == 404


def test_no_transaction_history_returns_409(
    forecast_client,
) -> None:
    """A forecast requires completed transaction history."""

    client, _ = forecast_client

    response = client.post(
        "/forecasts/liquidity-runway",
        json={
            "agent_code": "AGENT-FORECAST-002",
            "resource_type": "provider_float",
            "provider_code": "NAGAD_SIM",
            "lookback_hours": 4,
        },
    )

    assert response.status_code == 409


def test_invalid_lookback_returns_422(
    forecast_client,
) -> None:
    """The lookback window must be positive."""

    client, _ = forecast_client

    response = client.post(
        "/forecasts/liquidity-runway",
        json={
            "agent_code": "AGENT-FORECAST-001",
            "resource_type": "physical_cash",
            "lookback_hours": 0,
        },
    )

    assert response.status_code == 422