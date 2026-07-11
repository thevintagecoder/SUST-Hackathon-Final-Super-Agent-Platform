"""Persistent multilingual alert model."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
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
    from backend.app.models.alert_event import (
        AlertEvent,
    )


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""

    return datetime.now(
        UTC
    )


class Alert(Base):
    """Store one explainable multilingual alert."""

    __tablename__ = "alerts"

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ("
            "'LIQUIDITY_RUNWAY', "
            "'ANOMALY_REVIEW', "
            "'STALE_DATA', "
            "'SERVICEABILITY_SHORTFALL'"
            ")",
            name="ck_alerts_alert_type",
        ),
        CheckConstraint(
            "severity IN ("
            "'LOW', "
            "'MEDIUM', "
            "'HIGH', "
            "'CRITICAL'"
            ")",
            name="ck_alerts_severity",
        ),
        CheckConstraint(
            "status IN ("
            "'OPEN', "
            "'ACKNOWLEDGED', "
            "'ASSIGNED', "
            "'ESCALATED', "
            "'RESOLVED'"
            ")",
            name="ck_alerts_status",
        ),
        CheckConstraint(
            "confidence >= 0 "
            "AND confidence <= 1",
            name="ck_alerts_confidence",
        ),
        Index(
            "ix_alerts_agent_status_created_at",
            "agent_id",
            "status",
            "created_at",
        ),
        Index(
            "ix_alerts_scenario_id",
            "scenario_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    deduplication_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="OPEN",
        nullable=False,
    )

    agent_id: Mapped[int] = mapped_column(
        ForeignKey(
            "agents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "providers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    scenario_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    source_reference: Mapped[str | None] = (
        mapped_column(
            String(255),
            nullable=True,
        )
    )

    title_en: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    title_bn: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    title_bn_latn: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    message_en: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    message_bn: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    message_bn_latn: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    next_step_en: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    next_step_bn: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    next_step_bn_latn: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    evidence: Mapped[dict[str, object]] = (
        mapped_column(
            JSON,
            default=dict,
            nullable=False,
        )
    )

    confidence: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=5,
            scale=4,
        ),
        default=Decimal("0.0000"),
        nullable=False,
    )

    freshness_state: Mapped[str | None] = (
        mapped_column(
            String(30),
            nullable=True,
        )
    )

    human_review_required: Mapped[bool] = (
        mapped_column(
            Boolean,
            default=True,
            nullable=False,
        )
    )

    automatic_action_taken: Mapped[bool] = (
        mapped_column(
            Boolean,
            default=False,
            nullable=False,
        )
    )

    assigned_to: Mapped[str | None] = (
        mapped_column(
            String(120),
            nullable=True,
        )
    )

    acknowledged_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(
                timezone=True
            ),
            nullable=True,
        )
    )

    resolved_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(
                timezone=True
            ),
            nullable=True,
        )
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    events: Mapped[list["AlertEvent"]] = (
        relationship(
            back_populates="alert",
            cascade="all, delete-orphan",
            order_by="AlertEvent.created_at",
        )
    )