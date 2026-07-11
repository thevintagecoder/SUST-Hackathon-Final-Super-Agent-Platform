"""SQLAlchemy model for support-request timeline events."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class SupportRequestEvent(Base):
    """Represent one append-only event in a support-request timeline."""

    __tablename__ = "support_request_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN "
            "('created', 'accepted', 'rejected', "
            "'escalated', 'resolved', 'cancelled', "
            "'note_added')",
            name="ck_support_request_events_type",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    support_request_id: Mapped[int] = mapped_column(
        ForeignKey(
            "support_requests.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    actor_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    actor_role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    from_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    to_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )