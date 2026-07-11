"""API routes for persisted multilingual alerts."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status as http_status,
)
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.alert import (
    AlertDetailResponse,
    AlertGenerationRequest,
    AlertGenerationResponse,
    AlertListResponse,
    AlertStatus,
    AlertType,
)
from backend.app.services.alert_generation_service import (
    AlertGenerationDataUnavailableError,
    AlertGenerationNotFoundError,
    AlertGenerationValidationError,
    generate_persisted_alert,
)
from backend.app.services.alert_service import (
    AlertNotFoundError,
    get_alert_detail,
    list_alerts,
)
from backend.app.services.alert_templates import (
    AlertTemplateError,
)
from backend.app.services.anomaly_service import (
    AnomalyNotFoundError,
    AnomalyValidationError,
)
from backend.app.services.forecast_service import (
    ForecastDataUnavailableError,
    ForecastNotFoundError,
    ForecastValidationError,
)


router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
)


@router.post(
    "/generate",
    response_model=AlertGenerationResponse,
    status_code=http_status.HTTP_200_OK,
)
def generate_alert(
    request: AlertGenerationRequest,
    db: Session = Depends(
        get_db
    ),
) -> AlertGenerationResponse:
    """Evaluate evidence and persist an alert when needed."""

    try:
        return generate_persisted_alert(
            db=db,
            request=request,
        )

    except (
        AlertGenerationNotFoundError,
        ForecastNotFoundError,
        AnomalyNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=(
                http_status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error

    except (
        AlertGenerationDataUnavailableError,
        ForecastDataUnavailableError,
    ) as error:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except (
        AlertGenerationValidationError,
        ForecastValidationError,
        AnomalyValidationError,
        AlertTemplateError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=(
                http_status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=AlertListResponse,
    status_code=http_status.HTTP_200_OK,
)
def read_alerts(
    status_filter: AlertStatus | None = Query(
        default=None,
        alias="status",
    ),
    alert_type: AlertType | None = Query(
        default=None,
    ),
    agent_code: str | None = Query(
        default=None,
        min_length=1,
        max_length=50,
    ),
    provider_code: str | None = Query(
        default=None,
        min_length=1,
        max_length=30,
    ),
    scenario_id: str | None = Query(
        default=None,
        min_length=1,
        max_length=50,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(
        get_db
    ),
) -> AlertListResponse:
    """List alerts using optional workflow filters."""

    return list_alerts(
        db=db,
        status_filter=status_filter,
        alert_type=alert_type,
        agent_code=agent_code,
        provider_code=provider_code,
        scenario_id=scenario_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{alert_id}",
    response_model=AlertDetailResponse,
    status_code=http_status.HTTP_200_OK,
)
def read_alert_detail(
    alert_id: int,
    db: Session = Depends(
        get_db
    ),
) -> AlertDetailResponse:
    """Return one alert and its review timeline."""

    try:
        return get_alert_detail(
            db=db,
            alert_id=alert_id,
        )

    except AlertNotFoundError as error:
        raise HTTPException(
            status_code=(
                http_status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error