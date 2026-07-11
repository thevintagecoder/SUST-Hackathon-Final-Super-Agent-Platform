"""SQLAlchemy model for provider-specific electronic balances."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ProviderBalance(Base):
    """Represent one provider balance held by one Agent."""

    __tablename__ = "provider_balances"
    __table_args__ = (
        UniqueConstraint(
            "agent_id",
            "provider_id",
            name="uq_provider_balances_agent_provider",
        ),
        CheckConstraint(
            "electronic_balance >= 0",
            name="ck_provider_balances_nonnegative",
        ),
        CheckConstraint(
            "freshness_state IN "
            "('fresh', 'delayed', 'missing', 'conflicting')",
            name="ck_provider_balances_freshness_state",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    agent_id: Mapped[int] = mapped_column(
        ForeignKey(
            "agents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    provider_id: Mapped[int] = mapped_column(
        ForeignKey(
            "providers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    electronic_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    last_update_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    freshness_state: Mapped[str] = mapped_column(
        String(20),
        default="fresh",
        server_default="fresh",
        nullable=False,
    )