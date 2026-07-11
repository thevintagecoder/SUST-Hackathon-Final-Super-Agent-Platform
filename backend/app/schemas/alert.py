"""Schemas shared by the multilingual alert system."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


AlertType = Literal[
    "LIQUIDITY_RUNWAY",
    "ANOMALY_REVIEW",
    "STALE_DATA",
    "SERVICEABILITY_SHORTFALL",
]

AlertTransactionType = Literal[
    "cash_in",
    "cash_out",
]


class LocalizedAlertText(BaseModel):
    """Store one alert message in three supported languages."""

    en: str
    bn: str
    bn_latn: str


class RenderedAlertTemplate(BaseModel):
    """Store the localized presentation text for one alert."""

    alert_type: AlertType

    title: LocalizedAlertText
    message: LocalizedAlertText
    next_step: LocalizedAlertText


class AlertGenerationRequest(BaseModel):
    """Describe one request to evaluate and persist an alert."""

    alert_type: AlertType

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

    lookback_hours: int = Field(
        default=6,
        ge=1,
        le=168,
    )

    warning_threshold_hours: Decimal = Field(
        default=Decimal("8.00"),
        gt=0,
        le=168,
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
    )

    minimum_repeated_count: int = Field(
        default=5,
        ge=2,
        le=100,
    )

    velocity_multiplier: Decimal = Field(
        default=Decimal("2.00"),
        gt=Decimal("1.00"),
    )

    transaction_type: AlertTransactionType | None = None

    requested_amount: Decimal | None = Field(
        default=None,
        gt=0,
    )


class AlertGenerationResponse(BaseModel):
    """Describe the result of alert evaluation and persistence."""

    alert_type: AlertType

    condition_detected: bool
    alert_created: bool
    deduplicated: bool

    alert_id: int | None
    reason: str

    human_review_required: bool
    automatic_action_taken: bool = False