"""API tests for the transaction serviceability check."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.models import (
    Agent,
    AgentPosition,
    Provider,
    ProviderBalance,
)
from backend.app.routers.liquidity import router


@pytest.fixture
def test_context():
    """Create an isolated FastAPI application and database."""

    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    testing_session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(engine)

    def override_get_db():
        db = testing_session_factory()

        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, testing_session_factory

    Base.metadata.drop_all(engine)
    engine.dispose()


def seed_liquidity_data(
    session_factory,
) -> None:
    """Insert the judge's example into the test database."""

    now = datetime(
        2026,
        7,
        11,
        12,
        0,
        tzinfo=UTC,
    )

    with Session(session_factory.kw["bind"]) as db:
        agent = Agent(
            code="AGENT-SYL-001",
            name="Synthetic Sylhet Agent",
            area="Sylhet",
        )
        bkash = Provider(
            code="BKASH_SIM",
            name="Synthetic bKash Provider",
        )
        nagad = Provider(
            code="NAGAD_SIM",
            name="Synthetic Nagad Provider",
        )

        db.add_all(
            [
                agent,
                bkash,
                nagad,
            ]
        )
        db.flush()

        db.add(
            AgentPosition(
                agent_id=agent.id,
                shared_cash=Decimal("10000.00"),
                as_of=now,
            )
        )

        db.add_all(
            [
                ProviderBalance(
                    agent_id=agent.id,
                    provider_id=bkash.id,
                    electronic_balance=Decimal(
                        "3000.00"
                    ),
                    last_update_at=now,
                    freshness_state="fresh",
                ),
                ProviderBalance(
                    agent_id=agent.id,
                    provider_id=nagad.id,
                    electronic_balance=Decimal(
                        "2000.00"
                    ),
                    last_update_at=now,
                    freshness_state="fresh",
                ),
            ]
        )

        db.commit()


def test_nagad_cash_in_does_not_use_bkash_balance(
    test_context,
) -> None:
    """Other provider balances must not cover a Nagad shortfall."""

    client, session_factory = test_context
    seed_liquidity_data(session_factory)

    response = client.post(
        "/liquidity/check-serviceability",
        json={
            "agent_code": "AGENT-SYL-001",
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_in",
            "amount": 5000,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["serviceable"] is False
    assert body["status"] == "PARTIALLY_SERVICEABLE"
    assert Decimal(
        str(body["available_amount"])
    ) == Decimal("2000.00")
    assert Decimal(
        str(body["shortfall"])
    ) == Decimal("3000.00")
    assert (
        body["required_resource"]
        == "NAGAD_SIM electronic float"
    )


def test_cash_out_checks_shared_physical_cash(
    test_context,
) -> None:
    """Cash-out serviceability should depend on physical cash."""

    client, session_factory = test_context
    seed_liquidity_data(session_factory)

    response = client.post(
        "/liquidity/check-serviceability",
        json={
            "agent_code": "AGENT-SYL-001",
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_out",
            "amount": 5000,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["serviceable"] is True
    assert body["status"] == "SERVICEABLE"
    assert Decimal(
        str(body["available_amount"])
    ) == Decimal("10000.00")
    assert Decimal(
        str(body["shortfall"])
    ) == Decimal("0.00")
    assert (
        body["required_resource"]
        == "shared physical cash"
    )


def test_large_cash_out_returns_exact_shortfall(
    test_context,
) -> None:
    """An unserviceable request should explain the shortage."""

    client, session_factory = test_context
    seed_liquidity_data(session_factory)

    response = client.post(
        "/liquidity/check-serviceability",
        json={
            "agent_code": "AGENT-SYL-001",
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_out",
            "amount": 80000,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["serviceable"] is False
    assert body["status"] == "PARTIALLY_SERVICEABLE"
    assert Decimal(
        str(body["shortfall"])
    ) == Decimal("70000.00")


def test_unknown_agent_returns_404(
    test_context,
) -> None:
    """An unknown Agent should receive a clear API error."""

    client, _ = test_context

    response = client.post(
        "/liquidity/check-serviceability",
        json={
            "agent_code": "AGENT-UNKNOWN",
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_in",
            "amount": 5000,
        },
    )

    assert response.status_code == 404


def test_zero_amount_is_rejected(
    test_context,
) -> None:
    """The requested transaction amount must be positive."""

    client, _ = test_context

    response = client.post(
        "/liquidity/check-serviceability",
        json={
            "agent_code": "AGENT-SYL-001",
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_in",
            "amount": 0,
        },
    )

    assert response.status_code == 422