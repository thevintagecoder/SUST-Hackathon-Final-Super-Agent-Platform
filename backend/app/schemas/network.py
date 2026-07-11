"""Request and response schemas for Agent network support searches."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


TransactionType = Literal[
    "cash_in",
    "cash_out",
]

NetworkSupportStatus = Literal[
    "LOCAL_SERVICEABLE",
    "NETWORK_SUPPORT_AVAILABLE",
    "CONFIRMATION_REQUIRED",
    "NO_SUPPORT_FOUND",
]

CandidateRecommendationStatus = Literal[
    "RECOMMENDED",
    "REQUIRES_CONFIRMATION",
    "INSUFFICIENT_CAPACITY",
]


class NetworkSupportRequest(BaseModel):
    """Describe a request for Agent-to-Agent support discovery."""

    requesting_agent_code: str = Field(
        min_length=1,
        max_length=50,
    )
    provider_code: str = Field(
        min_length=1,
        max_length=30,
    )
    transaction_type: TransactionType
    amount: Decimal = Field(
        gt=0,
    )
    max_distance_km: Decimal = Field(
        default=Decimal("10.00"),
        gt=0,
        le=100,
    )


class SupportCandidateResponse(BaseModel):
    """Describe one potential supporting Agent."""

    agent_code: str
    name: str
    area: str

    distance_km: Decimal | None

    resource_balance: Decimal
    safety_reserve: Decimal
    supportable_capacity: Decimal

    can_cover_shortfall: bool

    freshness_state: str
    last_updated_at: datetime
    confidence: Decimal

    recommendation_status: CandidateRecommendationStatus
    recommended_mode: str
    explanation: str


class NetworkSupportResponse(BaseModel):
    """Explain local serviceability and possible network support."""

    status: NetworkSupportStatus

    requesting_agent_code: str
    provider_code: str
    transaction_type: TransactionType

    requested_amount: Decimal
    local_available_amount: Decimal
    shortfall: Decimal

    required_resource: str
    safety_reserve: Decimal

    local_serviceable: bool
    candidates: list[SupportCandidateResponse]

    explanation: str
    recommended_action: str
    human_confirmation_required: bool = True