"""Tests for persistent alert and alert-event models."""

from decimal import Decimal

from sqlalchemy import (
    create_engine,
    select,
)
from sqlalchemy.orm import (
    Session,
    selectinload,
)

from backend.app.db.base import Base
from backend.app.models import (
    Agent,
    Alert,
    AlertEvent,
)


def test_alert_model_defines_expected_columns() -> None:
    """Alert should expose all persistence fields."""

    column_names = set(
        Alert.__table__.columns.keys()
    )

    assert column_names == {
        "id",
        "deduplication_key",
        "alert_type",
        "severity",
        "status",
        "agent_id",
        "provider_id",
        "scenario_id",
        "source_reference",
        "title_en",
        "title_bn",
        "title_bn_latn",
        "message_en",
        "message_bn",
        "message_bn_latn",
        "next_step_en",
        "next_step_bn",
        "next_step_bn_latn",
        "evidence",
        "confidence",
        "freshness_state",
        "human_review_required",
        "automatic_action_taken",
        "assigned_to",
        "acknowledged_at",
        "resolved_at",
        "created_at",
        "updated_at",
    }

    assert (
        Alert.__table__
        .columns["deduplication_key"]
        .unique
        is True
    )


def test_alert_event_defines_expected_columns() -> None:
    """AlertEvent should expose timeline fields."""

    column_names = set(
        AlertEvent.__table__.columns.keys()
    )

    assert column_names == {
        "id",
        "alert_id",
        "event_type",
        "actor",
        "note",
        "event_data",
        "created_at",
    }


def test_alert_and_event_can_be_saved() -> None:
    """An alert and its timeline should persist together."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(
        engine
    )

    with Session(engine) as session:
        agent = Agent(
            code="AGENT-ALERT-001",
            name="Alert Test Agent",
            area="Test Area",
        )

        session.add(
            agent
        )
        session.flush()

        alert = Alert(
            deduplication_key=(
                "LIQUIDITY_RUNWAY:"
                "AGENT-ALERT-001:"
                "NAGAD_SIM:"
                "FORECAST-001"
            ),
            alert_type="LIQUIDITY_RUNWAY",
            severity="HIGH",
            status="OPEN",
            agent_id=agent.id,
            provider_id=None,
            scenario_id="FORECAST-001",
            source_reference=(
                "forecast:FORECAST-001"
            ),
            title_en=(
                "Nagad float may become "
                "insufficient soon"
            ),
            title_bn=(
                "নগদ ফ্লোট শীঘ্রই "
                "অপর্যাপ্ত হতে পারে"
            ),
            title_bn_latn=(
                "Nagad float shighroi "
                "oporjapto hote pare"
            ),
            message_en=(
                "Approximately 3.50 hours "
                "of runway may remain."
            ),
            message_bn=(
                "আনুমানিক ৩.৫০ ঘণ্টা "
                "সময় থাকতে পারে।"
            ),
            message_bn_latn=(
                "Anumaanik 3.50 ghonta "
                "shomoy thakte pare."
            ),
            next_step_en=(
                "Review the current balance."
            ),
            next_step_bn=(
                "বর্তমান ব্যালেন্স "
                "পর্যালোচনা করুন।"
            ),
            next_step_bn_latn=(
                "Bortoman balance "
                "review korun."
            ),
            evidence={
                "runway_hours": "3.50",
                "provider_code": "NAGAD_SIM",
            },
            confidence=Decimal("0.8500"),
            freshness_state="fresh",
            human_review_required=True,
            automatic_action_taken=False,
        )

        alert.events.append(
            AlertEvent(
                event_type="CREATED",
                actor="system",
                note=(
                    "Created from deterministic "
                    "forecast evidence."
                ),
                event_data={
                    "source": "forecast",
                },
            )
        )

        session.add(
            alert
        )
        session.commit()

        saved_alert = session.scalar(
            select(Alert)
            .options(
                selectinload(
                    Alert.events
                )
            )
            .where(
                Alert.deduplication_key
                == (
                    "LIQUIDITY_RUNWAY:"
                    "AGENT-ALERT-001:"
                    "NAGAD_SIM:"
                    "FORECAST-001"
                )
            )
        )

    assert saved_alert is not None
    assert saved_alert.id is not None
    assert saved_alert.status == "OPEN"

    assert (
        saved_alert.confidence
        == Decimal("0.8500")
    )

    assert saved_alert.evidence == {
        "runway_hours": "3.50",
        "provider_code": "NAGAD_SIM",
    }

    assert len(
        saved_alert.events
    ) == 1

    assert (
        saved_alert.events[0].event_type
        == "CREATED"
    )

    assert (
        saved_alert.events[0].actor
        == "system"
    )

    assert (
        saved_alert
        .automatic_action_taken
        is False
    )

    engine.dispose()


def test_deleting_alert_deletes_events() -> None:
    """Deleting an Alert should remove its child events."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(
        engine
    )

    with Session(engine) as session:
        agent = Agent(
            code="AGENT-ALERT-DELETE",
            name="Delete Test Agent",
            area="Test Area",
        )

        session.add(
            agent
        )
        session.flush()

        alert = Alert(
            deduplication_key=(
                "STALE_DATA:"
                "AGENT-ALERT-DELETE:"
                "NAGAD_SIM"
            ),
            alert_type="STALE_DATA",
            severity="MEDIUM",
            agent_id=agent.id,
            title_en="Provider data is delayed",
            title_bn="প্রোভাইডার তথ্য বিলম্বিত",
            title_bn_latn=(
                "Provider data delayed"
            ),
            message_en="Availability may be uncertain.",
            message_bn="প্রাপ্যতা অনিশ্চিত হতে পারে।",
            message_bn_latn=(
                "Availability onishchit hote pare."
            ),
            next_step_en="Verify the provider feed.",
            next_step_bn="প্রোভাইডার তথ্য যাচাই করুন।",
            next_step_bn_latn=(
                "Provider feed verify korun."
            ),
            evidence={},
            confidence=Decimal("0.6000"),
            freshness_state="delayed",
        )

        alert.events.append(
            AlertEvent(
                event_type="CREATED",
                actor="system",
            )
        )

        session.add(
            alert
        )
        session.commit()

        alert_id = alert.id

        session.delete(
            alert
        )
        session.commit()

        remaining_events = list(
            session.scalars(
                select(AlertEvent).where(
                    AlertEvent.alert_id
                    == alert_id
                )
            ).all()
        )

    assert remaining_events == []

    engine.dispose()