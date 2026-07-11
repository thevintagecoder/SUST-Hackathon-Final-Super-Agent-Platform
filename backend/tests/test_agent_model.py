"""Tests for the Agent SQLAlchemy model."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.db.base import Base
from backend.app.models import Agent


def test_agent_model_defines_expected_columns() -> None:
    """The Agent model should expose the required first fields."""

    column_names = set(Agent.__table__.columns.keys())

    assert column_names == {
    "id",
    "code",
    "name",
    "area",
    "latitude",
    "longitude",
    "is_active",
    "created_at",
}
    assert Agent.__table__.columns["code"].unique is True


def test_agent_can_be_saved_and_read() -> None:
    """A SQLAlchemy Session should persist and query an Agent."""

    test_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )
    Base.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        agent = Agent(
            code="AGENT-TEST-001",
            name="Synthetic Test Agent",
            area="Test Area",
        )

        session.add(agent)
        session.commit()

        saved_agent = session.scalar(
            select(Agent).where(
                Agent.code == "AGENT-TEST-001"
            )
        )

    assert saved_agent is not None
    assert saved_agent.id is not None
    assert saved_agent.name == "Synthetic Test Agent"
    assert saved_agent.area == "Test Area"
    assert saved_agent.is_active is True