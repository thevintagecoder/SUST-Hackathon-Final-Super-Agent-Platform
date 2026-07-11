"""Request and response schemas for liquidity checks."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


TransactionType = Literal[
    "cash_in",
    "cash_out",
]

ServiceabilityStatus = Literal[
    "SERVICEABLE",
    "PARTIALLY_SERVICEABLE",
    "NOT_SERVICEABLE",
]


class ServiceabilityRequest(BaseModel):
    """Describe a customer transaction request."""

    agent_code: str = Field(
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


class ServiceabilityResponse(BaseModel):
    """Explain whether the full request can be served."""

    serviceable: bool
    status: ServiceabilityStatus

    agent_code: str
    provider_code: str
    transaction_type: TransactionType

    requested_amount: Decimal
    available_amount: Decimal
    shortfall: Decimal

    required_resource: str
    explanation: str
    recommended_actions: list[str]

    human_confirmation_required: bool = True