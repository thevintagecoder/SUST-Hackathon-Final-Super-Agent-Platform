"""Tests for optional synthetic Agent location fields."""

from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.db.base import Base
from backend.app.models import Agent


def test_agent_location_can_be_persisted() -> None:
    """Store and retrieve synthetic Agent coordinates."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        agent = Agent(
            code="AGENT-SYL-LOCATION-TEST",
            name="Synthetic Location Test Agent",
            area="Sylhet",
            latitude=Decimal("24.894900"),
            longitude=Decimal("91.868700"),
        )

        session.add(agent)
        session.commit()

        stored_agent = session.scalar(
            select(Agent).where(
                Agent.code
                == "AGENT-SYL-LOCATION-TEST"
            )
        )

        assert stored_agent is not None
        assert stored_agent.latitude == Decimal(
            "24.894900"
        )
        assert stored_agent.longitude == Decimal(
            "91.868700"
        )

    engine.dispose()


def test_agent_location_is_optional() -> None:
    """Existing Agents may temporarily have no coordinates."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        agent = Agent(
            code="AGENT-NO-LOCATION-TEST",
            name="Synthetic Agent Without Location",
            area="Sylhet",
        )

        session.add(agent)
        session.commit()

        assert agent.id is not None
        assert agent.latitude is None
        assert agent.longitude is None

    engine.dispose()