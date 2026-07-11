"""Application entry point for the Super Agent platform API."""

from fastapi import FastAPI, status
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response returned when the API is operating normally."""

    status: str


app = FastAPI(
    title="Super Agent Liquidity & Risk Intelligence API",
    version="0.1.0",
    description=(
        "Decision-support API for a simulated multi-provider agent ecosystem. "
        "This prototype uses synthetic data and does not execute financial actions."
    ),
)


@app.get(
    "/health",
    response_model=HealthResponse, #a pydantic schema 
    status_code=status.HTTP_200_OK,
    tags=["System"],
)
def health_check() -> HealthResponse:
    """Confirm that the FastAPI application is running."""

    return HealthResponse(status="ok")