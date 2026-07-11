"""SQLAlchemy model for Agent-to-Agent support requests."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class SupportRequest(Base):
    """Represent one human-approved liquidity coordination request."""

    __tablename__ = "support_requests"
    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('cash_in', 'cash_out')",
            name="ck_support_requests_transaction_type",
        ),
        CheckConstraint(
            "resource_type IN "
            "('provider_float', 'physical_cash')",
            name="ck_support_requests_resource_type",
        ),
        CheckConstraint(
            "status IN "
            "('pending', 'accepted', 'rejected', "
            "'escalated', 'resolved', 'cancelled')",
            name="ck_support_requests_status",
        ),
        CheckConstraint(
            "requested_amount > 0",
            name="ck_support_requests_requested_amount_positive",
        ),
        CheckConstraint(
            "approved_amount IS NULL OR approved_amount > 0",
            name="ck_support_requests_approved_amount_positive",
        ),
        CheckConstraint(
            "approved_amount IS NULL "
            "OR approved_amount <= requested_amount",
            name="ck_support_requests_approved_not_above_requested",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    requesting_agent_id: Mapped[int] = mapped_column(
        ForeignKey(
            "agents.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    supporting_agent_id: Mapped[int] = mapped_column(
        ForeignKey(
            "agents.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    provider_id: Mapped[int] = mapped_column(
        ForeignKey(
            "providers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    resource_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    requested_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    approved_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default="pending",
        nullable=False,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    operations_owner: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )