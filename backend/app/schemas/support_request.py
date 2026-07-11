"""Schemas for human-approved liquidity support coordination."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


TransactionType = Literal[
    "cash_in",
    "cash_out",
]

SupportRequestStatus = Literal[
    "pending",
    "accepted",
    "rejected",
    "escalated",
    "resolved",
    "cancelled",
]


class SupportRequestCreate(BaseModel):
    """Create a coordination request between two Agents."""

    requesting_agent_code: str = Field(
        min_length=1,
        max_length=50,
    )

    supporting_agent_code: str = Field(
        min_length=1,
        max_length=50,
    )

    provider_code: str = Field(
        min_length=1,
        max_length=30,
    )

    transaction_type: TransactionType

    requested_amount: Decimal = Field(
        gt=0,
    )

    reason: str = Field(
        min_length=5,
        max_length=1000,
    )

    created_by: str = Field(
        min_length=1,
        max_length=100,
    )

    operations_owner: str | None = Field(
        default=None,
        max_length=100,
    )


class AcceptSupportRequest(BaseModel):
    """Accept all or part of a support request."""

    actor_code: str = Field(
        min_length=1,
        max_length=100,
    )

    approved_amount: Decimal | None = Field(
        default=None,
        gt=0,
    )

    note: str | None = Field(
        default=None,
        max_length=1000,
    )


class SupportRequestAction(BaseModel):
    """Perform a workflow transition."""

    actor_code: str = Field(
        min_length=1,
        max_length=100,
    )

    note: str | None = Field(
        default=None,
        max_length=1000,
    )


class SupportRequestNoteCreate(BaseModel):
    """Add a timeline note without changing status."""

    actor_code: str = Field(
        min_length=1,
        max_length=100,
    )

    actor_role: str = Field(
        default="operations",
        min_length=1,
        max_length=50,
    )

    note: str = Field(
        min_length=1,
        max_length=1000,
    )


class SupportRequestEventResponse(BaseModel):
    """Represent one item in the request timeline."""

    id: int
    event_type: str
    actor_code: str
    actor_role: str
    from_status: str | None
    to_status: str | None
    note: str | None
    created_at: datetime


class SupportRequestResponse(BaseModel):
    """Return a support request with its complete timeline."""

    id: int

    requesting_agent_code: str
    supporting_agent_code: str
    provider_code: str

    transaction_type: TransactionType
    resource_type: str

    requested_amount: Decimal
    approved_amount: Decimal | None

    status: SupportRequestStatus
    reason: str

    created_by: str
    operations_owner: str | None

    created_at: datetime
    updated_at: datetime

    events: list[SupportRequestEventResponse]


class SupportRequestListResponse(BaseModel):
    """Return support requests for Operations monitoring."""

    total: int
    items: list[SupportRequestResponse]