"""Human-review workflow actions for persisted alerts."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import (
    Alert,
    AlertEvent,
)
from backend.app.schemas.alert import (
    AlertEventResponse,
    AlertWorkflowResponse,
)


class AlertWorkflowNotFoundError(Exception):
    """Raised when a workflow alert cannot be found."""


class AlertWorkflowValidationError(Exception):
    """Raised when an alert workflow transition is invalid."""


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""

    return datetime.now(
        UTC
    )


def find_alert(
    *,
    db: Session,
    alert_id: int,
) -> Alert:
    """Return one persisted alert."""

    alert = db.scalar(
        select(Alert).where(
            Alert.id == alert_id
        )
    )

    if alert is None:
        raise AlertWorkflowNotFoundError(
            f"Alert '{alert_id}' was not found."
        )

    return alert


def require_not_resolved(
    *,
    alert: Alert,
    action_name: str,
) -> None:
    """Reject workflow changes after resolution."""

    if alert.status == "RESOLVED":
        raise AlertWorkflowValidationError(
            f"Cannot {action_name} a resolved alert."
        )


def append_event(
    *,
    db: Session,
    alert: Alert,
    event_type: str,
    actor: str,
    note: str | None = None,
    event_data: dict[str, object] | None = None,
) -> AlertEvent:
    """Append one event to the alert timeline."""

    event = AlertEvent(
        alert_id=alert.id,
        event_type=event_type,
        actor=actor.strip(),
        note=(
            note.strip()
            if note is not None
            else None
        ),
        event_data=event_data or {},
    )

    db.add(
        event
    )

    return event


def build_workflow_response(
    *,
    alert: Alert,
    event: AlertEvent,
) -> AlertWorkflowResponse:
    """Convert one workflow action into an API response."""

    return AlertWorkflowResponse(
        alert_id=alert.id,
        status=alert.status,
        assigned_to=alert.assigned_to,
        acknowledged_at=(
            alert.acknowledged_at
        ),
        resolved_at=alert.resolved_at,
        event=AlertEventResponse(
            id=event.id,
            event_type=event.event_type,
            actor=event.actor,
            note=event.note,
            event_data=dict(
                event.event_data or {}
            ),
            created_at=event.created_at,
        ),
        human_review_required=(
            alert.human_review_required
        ),
        automatic_action_taken=(
            alert.automatic_action_taken
        ),
    )


def commit_action(
    *,
    db: Session,
    alert: Alert,
    event: AlertEvent,
) -> AlertWorkflowResponse:
    """Commit one alert action atomically."""

    alert.updated_at = utc_now()

    db.commit()

    db.refresh(
        alert
    )

    db.refresh(
        event
    )

    return build_workflow_response(
        alert=alert,
        event=event,
    )


def acknowledge_alert(
    *,
    db: Session,
    alert_id: int,
    actor: str,
    note: str | None,
) -> AlertWorkflowResponse:
    """Acknowledge that a human has seen an alert."""

    alert = find_alert(
        db=db,
        alert_id=alert_id,
    )

    require_not_resolved(
        alert=alert,
        action_name="acknowledge",
    )

    if alert.status != "OPEN":
        raise AlertWorkflowValidationError(
            "Only an OPEN alert can be acknowledged."
        )

    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_at = utc_now()

    event = append_event(
        db=db,
        alert=alert,
        event_type="ACKNOWLEDGED",
        actor=actor,
        note=note,
        event_data={
            "previous_status": "OPEN",
            "new_status": "ACKNOWLEDGED",
        },
    )

    return commit_action(
        db=db,
        alert=alert,
        event=event,
    )


def assign_alert(
    *,
    db: Session,
    alert_id: int,
    actor: str,
    assigned_to: str,
    note: str | None,
) -> AlertWorkflowResponse:
    """Assign an alert to a human owner."""

    alert = find_alert(
        db=db,
        alert_id=alert_id,
    )

    require_not_resolved(
        alert=alert,
        action_name="assign",
    )

    previous_status = alert.status
    previous_owner = alert.assigned_to

    alert.status = "ASSIGNED"
    alert.assigned_to = assigned_to.strip()

    event = append_event(
        db=db,
        alert=alert,
        event_type="ASSIGNED",
        actor=actor,
        note=note,
        event_data={
            "previous_status": previous_status,
            "new_status": "ASSIGNED",
            "previous_owner": previous_owner,
            "assigned_to": alert.assigned_to,
        },
    )

    return commit_action(
        db=db,
        alert=alert,
        event=event,
    )


def add_alert_note(
    *,
    db: Session,
    alert_id: int,
    actor: str,
    note: str,
) -> AlertWorkflowResponse:
    """Append a note without changing workflow status."""

    alert = find_alert(
        db=db,
        alert_id=alert_id,
    )

    event = append_event(
        db=db,
        alert=alert,
        event_type="NOTE_ADDED",
        actor=actor,
        note=note,
        event_data={
            "status": alert.status,
        },
    )

    return commit_action(
        db=db,
        alert=alert,
        event=event,
    )


def escalate_alert(
    *,
    db: Session,
    alert_id: int,
    actor: str,
    note: str | None,
) -> AlertWorkflowResponse:
    """Escalate an unresolved alert for additional review."""

    alert = find_alert(
        db=db,
        alert_id=alert_id,
    )

    require_not_resolved(
        alert=alert,
        action_name="escalate",
    )

    if alert.status == "ESCALATED":
        raise AlertWorkflowValidationError(
            "The alert is already escalated."
        )

    previous_status = alert.status
    alert.status = "ESCALATED"

    event = append_event(
        db=db,
        alert=alert,
        event_type="ESCALATED",
        actor=actor,
        note=note,
        event_data={
            "previous_status": previous_status,
            "new_status": "ESCALATED",
        },
    )

    return commit_action(
        db=db,
        alert=alert,
        event=event,
    )


def resolve_alert(
    *,
    db: Session,
    alert_id: int,
    actor: str,
    note: str | None,
) -> AlertWorkflowResponse:
    """Resolve an alert after human review."""

    alert = find_alert(
        db=db,
        alert_id=alert_id,
    )

    require_not_resolved(
        alert=alert,
        action_name="resolve",
    )

    previous_status = alert.status

    alert.status = "RESOLVED"
    alert.resolved_at = utc_now()
    alert.human_review_required = False

    event = append_event(
        db=db,
        alert=alert,
        event_type="RESOLVED",
        actor=actor,
        note=note,
        event_data={
            "previous_status": previous_status,
            "new_status": "RESOLVED",
        },
    )

    return commit_action(
        db=db,
        alert=alert,
        event=event,
    )