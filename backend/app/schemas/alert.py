"""Schemas shared by the multilingual alert system."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


AlertType = Literal[
    "LIQUIDITY_RUNWAY",
    "ANOMALY_REVIEW",
    "STALE_DATA",
    "SERVICEABILITY_SHORTFALL",
]

AlertSeverity = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]

AlertStatus = Literal[
    "OPEN",
    "ACKNOWLEDGED",
    "ASSIGNED",
    "ESCALATED",
    "RESOLVED",
]

AlertTransactionType = Literal[
    "cash_in",
    "cash_out",
]


class LocalizedAlertText(BaseModel):
    """Store alert text in all supported languages."""

    en: str
    bn: str
    bn_latn: str


class RenderedAlertTemplate(BaseModel):
    """Store localized presentation text for one alert."""

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
    """Describe alert evaluation and persistence."""

    alert_type: AlertType

    condition_detected: bool
    alert_created: bool
    deduplicated: bool

    alert_id: int | None
    reason: str

    human_review_required: bool
    automatic_action_taken: bool = False


class AlertEventResponse(BaseModel):
    """Return one event from an alert timeline."""

    id: int
    event_type: str
    actor: str
    note: str | None
    event_data: dict[str, object]
    created_at: datetime


class AlertSummaryResponse(BaseModel):
    """Return one alert in a list view."""

    id: int

    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus

    agent_code: str
    provider_code: str | None
    scenario_id: str | None

    title: LocalizedAlertText

    confidence: Decimal
    freshness_state: str | None

    human_review_required: bool
    automatic_action_taken: bool

    assigned_to: str | None

    created_at: datetime
    updated_at: datetime


class AlertDetailResponse(AlertSummaryResponse):
    """Return a complete alert and its timeline."""

    source_reference: str | None

    message: LocalizedAlertText
    next_step: LocalizedAlertText

    evidence: dict[str, object]

    acknowledged_at: datetime | None
    resolved_at: datetime | None

    events: list[AlertEventResponse]


class AlertListResponse(BaseModel):
    """Return a paginated collection of alerts."""

    items: list[AlertSummaryResponse]

    total: int
    limit: int
    offset: int