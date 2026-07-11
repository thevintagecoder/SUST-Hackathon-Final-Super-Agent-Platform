"""API routes for explainable anomaly detection."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.anomaly import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
)
from backend.app.services.anomaly_service import (
    AnomalyNotFoundError,
    AnomalyValidationError,
    detect_anomalies_for_request,
)


router = APIRouter(
    prefix="/anomalies",
    tags=["anomalies"],
)


@router.post(
    "/detect",
    response_model=AnomalyDetectionResponse,
    status_code=status.HTTP_200_OK,
)
def detect_anomalies(
    request: AnomalyDetectionRequest,
    db: Session = Depends(get_db),
) -> AnomalyDetectionResponse:
    """Detect explainable unusual transaction patterns."""

    try:
        return detect_anomalies_for_request(
            db=db,
            request=request,
        )

    except AnomalyNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except (
        AnomalyValidationError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error