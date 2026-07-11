"""Schemas for explainable liquidity runway forecasts."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


ForecastResourceType = Literal[
    "provider_float",
    "physical_cash",
]

ForecastRiskLevel = Literal[
    "INSUFFICIENT_HISTORY",
    "STABLE_OR_REPLENISHING",
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]


class LiquidityRunwayRequest(BaseModel):
    """Describe one liquidity runway forecast request."""

    agent_code: str = Field(
        min_length=1,
        max_length=50,
    )

    resource_type: ForecastResourceType

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


class LiquidityRunwayResponse(BaseModel):
    """Return an explainable liquidity runway estimate."""

    agent_code: str
    resource_type: ForecastResourceType
    provider_code: str | None
    scenario_id: str | None

    current_balance: Decimal
    safety_threshold: Decimal
    balance_above_threshold: Decimal
    balance_as_of: datetime
    freshness_state: str

    forecast_as_of: datetime
    window_start: datetime
    window_end: datetime
    lookback_hours: int
    completed_transaction_count: int

    gross_consumption: Decimal
    gross_replenishment: Decimal
    net_consumption: Decimal
    net_consumption_per_hour: Decimal

    runway_hours: Decimal | None
    estimated_threshold_breach_time: datetime | None

    risk_level: ForecastRiskLevel
    confidence: Decimal

    warning_message: str
    explanation_factors: list[str]

    human_review_required: bool
    automatic_action_taken: bool = False