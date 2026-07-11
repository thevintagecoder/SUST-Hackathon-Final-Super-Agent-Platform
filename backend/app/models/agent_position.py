"""SQLAlchemy model for an Agent's shared physical-cash position."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class AgentPosition(Base):
    """Represent one Agent's current shared physical-cash position."""

    __tablename__ = "agent_positions"
    __table_args__ = (
        CheckConstraint(
            "shared_cash >= 0",
            name="ck_agent_positions_shared_cash_nonnegative",
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
        unique=True,
        nullable=False,
        index=True,
    )
    shared_cash: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    as_of: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )