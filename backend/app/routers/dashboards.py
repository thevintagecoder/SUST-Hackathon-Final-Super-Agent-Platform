"""API routes for stakeholder dashboards."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.dashboard import (
    AgentDashboardResponse,
    OperationsDashboardResponse,
)
from backend.app.services.dashboard_service import (
    DashboardNotFoundError,
    get_agent_dashboard,
    get_operations_dashboard,
)


router = APIRouter(
    prefix="/dashboards",
    tags=["dashboards"],
)


@router.get(
    "/agents/{agent_code}",
    response_model=AgentDashboardResponse,
    status_code=status.HTTP_200_OK,
)
def read_agent_dashboard(
    agent_code: str,
    scenario_id: str | None = Query(
        default=None,
        min_length=1,
        max_length=50,
    ),
    recent_alert_limit: int = Query(
        default=5,
        ge=1,
        le=20,
    ),
    db: Session = Depends(
        get_db
    ),
) -> AgentDashboardResponse:
    """Return one Agent/Super Agent dashboard."""

    try:
        return get_agent_dashboard(
            db=db,
            agent_code=agent_code,
            scenario_id=scenario_id,
            recent_alert_limit=(
                recent_alert_limit
            ),
        )

    except DashboardNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    
@router.get(
    "/operations",
    response_model=OperationsDashboardResponse,
    status_code=status.HTTP_200_OK,
)
def read_operations_dashboard(
    scenario_id: str | None = Query(
        default=None,
        min_length=1,
        max_length=50,
    ),
    recent_alert_limit: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
    db: Session = Depends(
        get_db
    ),
) -> OperationsDashboardResponse:
    """Return the cross-Agent Operations dashboard."""

    return get_operations_dashboard(
        db=db,
        scenario_id=scenario_id,
        recent_alert_limit=(
            recent_alert_limit
        ),
    )