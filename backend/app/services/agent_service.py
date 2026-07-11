"""Business operations for simulated Agents."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models import Agent
from backend.app.schemas.agent import AgentCreate


class AgentCodeAlreadyExistsError(ValueError):
    """Raised when an Agent code is already registered."""


def create_agent(
    db: Session,
    payload: AgentCreate,
) -> Agent:
    """Create and persist one simulated Agent."""

    existing_agent = db.scalar(
        select(Agent).where(
            Agent.code == payload.code
        )
    )

    if existing_agent is not None:
        raise AgentCodeAlreadyExistsError(payload.code)

    agent = Agent(
        code=payload.code,
        name=payload.name,
        area=payload.area,
    )

    db.add(agent)

    try:
        db.commit()
        db.refresh(agent)
    except IntegrityError as exc:
        db.rollback()
        raise AgentCodeAlreadyExistsError(
            payload.code
        ) from exc

    return agent