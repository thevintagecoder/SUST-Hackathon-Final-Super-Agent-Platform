"""Timeline event model for persistent alerts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.alert import Alert


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""

    return datetime.now(
        UTC
    )


class AlertEvent(Base):
    """Store one human or system action on an alert."""

    __tablename__ = "alert_events"

    __table_args__ = (
        Index(
            "ix_alert_events_alert_created_at",
            "alert_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    alert_id: Mapped[int] = mapped_column(
        ForeignKey(
            "alerts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    actor: Mapped[str] = mapped_column(
        String(120),
        default="system",
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    event_data: Mapped[dict[str, object]] = (
        mapped_column(
            JSON,
            default=dict,
            nullable=False,
        )
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=utc_now,
        nullable=False,
    )

    alert: Mapped["Alert"] = relationship(
        back_populates="events",
    )