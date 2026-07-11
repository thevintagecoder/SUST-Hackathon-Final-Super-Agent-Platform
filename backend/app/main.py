"""Application entry point for the Super Agent platform API."""

from fastapi import FastAPI, status
from pydantic import BaseModel

from backend.app.core.config import get_settings


class HealthResponse(BaseModel):
    """Response returned when the API is operating normally."""

    status: str


settings = get_settings()

app = FastAPI(
    title=settings.name,
    version=settings.version,
    debug=settings.debug,
    description=(
        "Decision-support API for a simulated multi-provider agent ecosystem. "
        "This prototype uses synthetic data and does not execute financial actions."
    ),
)


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
)
def health_check() -> HealthResponse:
    """Confirm that the FastAPI application is running."""

    return HealthResponse(status="ok")