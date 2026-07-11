"""FastAPI routes for Agent network support discovery."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.network import (
    NetworkSupportRequest,
    NetworkSupportResponse,
)
from backend.app.services.liquidity_service import (
    LiquidityDataUnavailableError,
    ServiceabilityNotFoundError,
)
from backend.app.services.network_service import (
    NetworkDataUnavailableError,
    find_network_support,
)


router = APIRouter(
    prefix="/network",
    tags=["Agent Network"],
)


@router.post(
    "/find-support",
    response_model=NetworkSupportResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": (
                "Requesting Agent or provider not found."
            ),
        },
        409: {
            "description": (
                "Required Agent or liquidity data "
                "is unavailable."
            ),
        },
    },
)
def find_support(
    request: NetworkSupportRequest,
    db: Session = Depends(get_db),
) -> NetworkSupportResponse:
    """Find possible Agent-to-Agent support options."""

    try:
        return find_network_support(
            db=db,
            request=request,
        )

    except ServiceabilityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except (
        LiquidityDataUnavailableError,
        NetworkDataUnavailableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc