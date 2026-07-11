"""FastAPI routes for explainable liquidity forecasts."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.forecast import (
    LiquidityRunwayRequest,
    LiquidityRunwayResponse,
)
from backend.app.services.forecast_service import (
    ForecastDataUnavailableError,
    ForecastNotFoundError,
    ForecastValidationError,
    forecast_liquidity_runway,
)


router = APIRouter(
    prefix="/forecasts",
    tags=["Forecasts"],
)


@router.post(
    "/liquidity-runway",
    response_model=LiquidityRunwayResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "The forecast request is inconsistent.",
        },
        404: {
            "description": "The Agent or provider was not found.",
        },
        409: {
            "description": "Required forecast data is unavailable.",
        },
    },
)
def create_liquidity_runway_forecast(
    request: LiquidityRunwayRequest,
    db: Session = Depends(get_db),
) -> LiquidityRunwayResponse:
    """Estimate when liquidity may cross its safety threshold."""

    try:
        return forecast_liquidity_runway(
            db=db,
            request=request,
        )

    except ForecastNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ForecastValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except ForecastDataUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc