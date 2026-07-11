"""FastAPI routes for liquidity decision support."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.liquidity import (
    ServiceabilityRequest,
    ServiceabilityResponse,
)
from backend.app.services.liquidity_service import (
    LiquidityDataUnavailableError,
    ServiceabilityNotFoundError,
    check_serviceability,
)


router = APIRouter(
    prefix="/liquidity",
    tags=["Liquidity"],
)


@router.post(
    "/check-serviceability",
    response_model=ServiceabilityResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Agent or provider not found.",
        },
        409: {
            "description": (
                "Required liquidity data is unavailable."
            ),
        },
    },
)
def check_transaction_serviceability(
    request: ServiceabilityRequest,
    db: Session = Depends(get_db),
) -> ServiceabilityResponse:
    """Determine whether an Agent can serve a transaction."""

    try:
        return check_serviceability(
            db=db,
            request=request,
        )

    except ServiceabilityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except LiquidityDataUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc