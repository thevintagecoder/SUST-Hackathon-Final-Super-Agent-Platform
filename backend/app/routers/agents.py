"""HTTP endpoints for simulated Agents."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.agent import (
    AgentCreate,
    AgentResponse,
)
from backend.app.services.agent_service import (
    AgentCodeAlreadyExistsError,
    create_agent,
)


router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_endpoint(
    payload: AgentCreate,
    db: Annotated[Session, Depends(get_db)],
) -> AgentResponse:
    """Create one simulated Agent."""

    try:
        agent = create_agent(
            db=db,
            payload=payload,
        )
    except AgentCodeAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent code already exists.",
        ) from exc

    return AgentResponse.model_validate(agent)