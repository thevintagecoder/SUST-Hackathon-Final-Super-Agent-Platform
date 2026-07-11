"""Request and response schemas for anomaly detection."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from backend.app.analytics.anomaly_detector import (
    AnomalyCategory,
    AnomalyDecision,
    AnomalySeverity,
)


class AnomalyDetectionRequest(BaseModel):
    """Describe one database-backed anomaly analysis."""

    agent_code: str = Field(
        min_length=1,
        max_length=50,
    )

    provider_code: str | None = Field(
        default=None,
        max_length=30,
    )

    scenario_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    recent_window_minutes: int = Field(
        default=60,
        ge=1,
        le=1440,
    )

    baseline_window_minutes: int = Field(
        default=60,
        ge=1,
        le=1440,
    )

    amount_tolerance: Decimal = Field(
        default=Decimal("100.00"),
        ge=0,
        le=Decimal("1000000.00"),
    )

    minimum_repeated_count: int = Field(
        default=5,
        ge=2,
        le=100,
    )

    velocity_multiplier: Decimal = Field(
        default=Decimal("2.00"),
        gt=Decimal("1.00"),
        le=Decimal("100.00"),
    )


class AnomalyDetectionResponse(BaseModel):
    """Return an explainable anomaly-detection result."""

    agent_code: str
    provider_code: str | None
    scenario_id: str | None

    anomaly_detected: bool
    category: AnomalyCategory | None
    severity: AnomalySeverity
    decision: AnomalyDecision

    analysis_as_of: datetime | None
    recent_window_start: datetime | None
    baseline_window_start: datetime | None

    recent_window_minutes: int
    baseline_window_minutes: int

    recent_transaction_count: int
    baseline_transaction_count: int
    velocity_ratio: Decimal | None

    repeated_amount_signal: bool
    velocity_signal: bool

    repeated_transaction_count: int
    repeated_amount_min: Decimal | None
    repeated_amount_max: Decimal | None
    repeated_transaction_ids: list[str]

    confidence: Decimal

    warning_message: str
    explanation_factors: list[str]
    uncertainty: str
    recommended_next_step: str

    human_review_required: bool
    automatic_action_taken: bool