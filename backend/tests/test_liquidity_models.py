"""Tests for the core liquidity SQLAlchemy models."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.base import Base
from backend.app.models import (
    Agent,
    AgentPosition,
    Provider,
    ProviderBalance,
    Transaction,
)


@pytest.fixture
def test_engine():
    """Create an isolated in-memory database."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    return engine


def test_core_liquidity_tables_are_registered(
    test_engine,
) -> None:
    """All required liquidity tables should exist in metadata."""

    table_names = set(
        inspect(test_engine).get_table_names()
    )

    assert {
        "agents",
        "providers",
        "agent_positions",
        "provider_balances",
        "transactions",
    }.issubset(table_names)


def test_liquidity_records_can_be_persisted(
    test_engine,
) -> None:
    """Persist an Agent, provider, balances, and transaction."""

    occurred_at = datetime(
        2026,
        7,
        11,
        10,
        0,
        tzinfo=UTC,
    )

    with Session(test_engine) as session:
        agent = Agent(
            code="AGENT-TEST-001",
            name="Synthetic Test Agent",
            area="Test Area",
        )
        provider = Provider(
            code="BKASH_SIM",
            name="Synthetic Provider One",
        )

        session.add_all([agent, provider])
        session.flush()

        position = AgentPosition(
            agent_id=agent.id,
            shared_cash=Decimal("50000.00"),
            as_of=occurred_at,
        )
        balance = ProviderBalance(
            agent_id=agent.id,
            provider_id=provider.id,
            electronic_balance=Decimal("25000.00"),
            last_update_at=occurred_at,
            freshness_state="fresh",
        )
        transaction = Transaction(
            external_id="TXN-TEST-001",
            scenario_id="NORMAL-001",
            agent_id=agent.id,
            provider_id=provider.id,
            synthetic_customer_id="CUSTOMER-TEST-001",
            transaction_type="cash_in",
            amount=Decimal("5000.00"),
            occurred_at=occurred_at,
            status="completed",
        )

        session.add_all(
            [
                position,
                balance,
                transaction,
            ]
        )
        session.commit()

        assert position.id is not None
        assert balance.id is not None
        assert transaction.id is not None
        assert position.shared_cash == Decimal("50000.00")
        assert balance.electronic_balance == Decimal("25000.00")
        assert transaction.amount == Decimal("5000.00")


def test_provider_balance_is_unique_per_agent_provider(
    test_engine,
) -> None:
    """Reject duplicate balances for one Agent-provider pair."""

    with Session(test_engine) as session:
        agent = Agent(
            code="AGENT-TEST-002",
            name="Synthetic Test Agent Two",
            area="Test Area",
        )
        provider = Provider(
            code="NAGAD_SIM",
            name="Synthetic Provider Two",
        )

        session.add_all([agent, provider])
        session.flush()

        session.add(
            ProviderBalance(
                agent_id=agent.id,
                provider_id=provider.id,
                electronic_balance=Decimal("10000.00"),
                freshness_state="fresh",
            )
        )
        session.commit()

        session.add(
            ProviderBalance(
                agent_id=agent.id,
                provider_id=provider.id,
                electronic_balance=Decimal("20000.00"),
                freshness_state="fresh",
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()