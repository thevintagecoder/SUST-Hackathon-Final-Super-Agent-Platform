"""Application entry point for the Super Agent platform API."""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from psycopg import Error as PsycopgError

from backend.app.core.config import get_settings
from backend.app.db.connection import check_database_connection
from backend.app.routers.agents import router as agents_router
from backend.app.routers.liquidity import router as liquidity_router
from backend.app.routers.network import router as network_router
from backend.app.routers.support_requests import (
    router as support_requests_router,
)
from backend.app.routers.forecasts import (
    router as forecasts_router,
)
from backend.app.routers.anomalies import (
    router as anomalies_router,
)


class HealthResponse(BaseModel):
    """Response returned when the API process is operating."""

    status: str


class DatabaseHealthResponse(BaseModel):
    """Response returned when PostgreSQL is reachable."""

    status: str
    database: str


settings = get_settings()

app = FastAPI(
    title=settings.name,
    version=settings.version,
    debug=settings.debug,
    description=(
        "Decision-support API for a simulated multi-provider "
        "agent ecosystem. This prototype uses synthetic data "
        "and does not execute financial actions."
    ),
)

app.include_router(agents_router)
app.include_router(liquidity_router)
app.include_router(network_router)
app.include_router(support_requests_router)
app.include_router(forecasts_router)
app.include_router(anomalies_router)


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
)
def health_check() -> HealthResponse:
    """Confirm that the FastAPI process is running."""

    return HealthResponse(status="ok")


@app.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
)
def database_health_check() -> DatabaseHealthResponse:
    """Confirm that FastAPI can connect to PostgreSQL."""

    try:
        connected = check_database_connection()
    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc

    if not connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database health check failed.",
        )

    return DatabaseHealthResponse(
        status="ok",
        database="reachable",
    )