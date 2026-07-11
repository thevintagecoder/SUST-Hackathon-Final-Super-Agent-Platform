"""Tests for loading generated synthetic scenarios."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from backend.app.data_loading.synthetic_loader import (
    load_synthetic_scenario,
)
from backend.app.db.base import Base
from backend.app.models import (
    Agent,
    AgentPosition,
    Provider,
    ProviderBalance,
    Transaction,
)
from synthetic_data.generator import generate_bundle


@pytest.fixture
def generated_directory(
    tmp_path: Path,
) -> Path:
    """Generate a temporary synthetic bundle."""

    generate_bundle(
        output_directory=tmp_path,
        seed=42,
    )

    return tmp_path


@pytest.fixture
def test_engine():
    """Create an isolated database for loader tests."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    return engine


def test_loader_persists_selected_scenario(
    generated_directory: Path,
    test_engine,
) -> None:
    """Load the repeated-amount scenario."""

    with Session(test_engine) as session:
        summary = load_synthetic_scenario(
            db=session,
            input_directory=generated_directory,
            scenario_id="REPEATED-001",
        )

        assert summary.agent_created is True
        assert summary.providers_created == 3
        assert summary.position_created is True
        assert summary.balances_created == 3
        assert summary.transactions_inserted == 29
        assert summary.transactions_skipped == 0

        agent_count = session.scalar(
            select(func.count(Agent.id))
        )
        provider_count = session.scalar(
            select(func.count(Provider.id))
        )
        balance_count = session.scalar(
            select(
                func.count(ProviderBalance.id)
            )
        )
        transaction_count = session.scalar(
            select(func.count(Transaction.id))
        )

        assert agent_count == 1
        assert provider_count == 3
        assert balance_count == 3
        assert transaction_count == 29

        position = session.scalar(
            select(AgentPosition)
        )

        assert position is not None
        assert float(position.shared_cash) == 65000.00

        scenario_ids = set(
            session.scalars(
                select(Transaction.scenario_id)
            ).all()
        )

        assert scenario_ids == {
            "REPEATED-001"
        }


def test_loader_is_idempotent(
    generated_directory: Path,
    test_engine,
) -> None:
    """Running the same load twice should not duplicate rows."""

    with Session(test_engine) as session:
        first_summary = load_synthetic_scenario(
            db=session,
            input_directory=generated_directory,
            scenario_id="REPEATED-001",
        )
        second_summary = load_synthetic_scenario(
            db=session,
            input_directory=generated_directory,
            scenario_id="REPEATED-001",
        )

        assert first_summary.transactions_inserted == 29
        assert second_summary.transactions_inserted == 0
        assert second_summary.transactions_skipped == 29

        transaction_count = session.scalar(
            select(func.count(Transaction.id))
        )

        assert transaction_count == 29


def test_loader_rejects_unknown_scenario(
    generated_directory: Path,
    test_engine,
) -> None:
    """An unknown scenario should fail clearly."""

    with Session(test_engine) as session:
        with pytest.raises(
            ValueError,
            match="Expected exactly one initial position",
        ):
            load_synthetic_scenario(
                db=session,
                input_directory=generated_directory,
                scenario_id="UNKNOWN-001",
            )

def test_loader_persists_network_scenario(
    generated_directory: Path,
    test_engine,
) -> None:
    """Load all four Agents in NETWORK-001."""

    with Session(test_engine) as session:
        summary = load_synthetic_scenario(
            db=session,
            input_directory=generated_directory,
            scenario_id="NETWORK-001",
        )

        assert summary.agents_created == 4
        assert summary.agents_updated == 0
        assert summary.providers_created == 3
        assert summary.positions_created == 4
        assert summary.positions_updated == 0
        assert summary.balances_created == 12
        assert summary.balances_updated == 0
        assert summary.transactions_inserted == 32
        assert summary.transactions_skipped == 0

        agent_count = session.scalar(
            select(func.count(Agent.id))
        )
        position_count = session.scalar(
            select(
                func.count(AgentPosition.id)
            )
        )
        balance_count = session.scalar(
            select(
                func.count(ProviderBalance.id)
            )
        )
        transaction_count = session.scalar(
            select(func.count(Transaction.id))
        )

        assert agent_count == 4
        assert position_count == 4
        assert balance_count == 12
        assert transaction_count == 32

        requesting_agent = session.scalar(
            select(Agent).where(
                Agent.code == "AGENT-SYL-001"
            )
        )

        assert requesting_agent is not None
        assert float(
            requesting_agent.latitude
        ) == pytest.approx(24.894900)
        assert float(
            requesting_agent.longitude
        ) == pytest.approx(91.868700)

        supporting_agent = session.scalar(
            select(Agent).where(
                Agent.code == "AGENT-SYL-002"
            )
        )
        nagad_provider = session.scalar(
            select(Provider).where(
                Provider.code == "NAGAD_SIM"
            )
        )

        assert supporting_agent is not None
        assert nagad_provider is not None

        supporting_balance = session.scalar(
            select(ProviderBalance).where(
                ProviderBalance.agent_id
                == supporting_agent.id,
                ProviderBalance.provider_id
                == nagad_provider.id,
            )
        )

        assert supporting_balance is not None
        assert float(
            supporting_balance.electronic_balance
        ) == 120000.00
        assert (
            supporting_balance.freshness_state
            == "fresh"
        )

        stale_agent = session.scalar(
            select(Agent).where(
                Agent.code == "AGENT-SYL-004"
            )
        )

        assert stale_agent is not None

        stale_balance = session.scalar(
            select(ProviderBalance).where(
                ProviderBalance.agent_id
                == stale_agent.id,
                ProviderBalance.provider_id
                == nagad_provider.id,
            )
        )

        assert stale_balance is not None
        assert float(
            stale_balance.electronic_balance
        ) == 150000.00
        assert (
            stale_balance.freshness_state
            == "delayed"
        )


def test_network_loader_is_idempotent(
    generated_directory: Path,
    test_engine,
) -> None:
    """Loading NETWORK-001 twice should not duplicate data."""

    with Session(test_engine) as session:
        first_summary = load_synthetic_scenario(
            db=session,
            input_directory=generated_directory,
            scenario_id="NETWORK-001",
        )
        second_summary = load_synthetic_scenario(
            db=session,
            input_directory=generated_directory,
            scenario_id="NETWORK-001",
        )

        assert (
            first_summary.transactions_inserted
            == 32
        )
        assert (
            second_summary.transactions_inserted
            == 0
        )
        assert (
            second_summary.transactions_skipped
            == 32
        )

        assert second_summary.agents_created == 0
        assert second_summary.agents_updated == 4
        assert second_summary.positions_created == 0
        assert second_summary.positions_updated == 4
        assert second_summary.balances_created == 0
        assert second_summary.balances_updated == 12

        agent_count = session.scalar(
            select(func.count(Agent.id))
        )
        position_count = session.scalar(
            select(
                func.count(AgentPosition.id)
            )
        )
        balance_count = session.scalar(
            select(
                func.count(ProviderBalance.id)
            )
        )
        transaction_count = session.scalar(
            select(func.count(Transaction.id))
        )

        assert agent_count == 4
        assert position_count == 4
        assert balance_count == 12
        assert transaction_count == 32