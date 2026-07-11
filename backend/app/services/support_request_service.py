"""Business logic for Agent-to-Agent support-request workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import (
    Agent,
    Provider,
    SupportRequest,
    SupportRequestEvent,
)
from backend.app.schemas.support_request import (
    AcceptSupportRequest,
    SupportRequestAction,
    SupportRequestCreate,
    SupportRequestEventResponse,
    SupportRequestListResponse,
    SupportRequestNoteCreate,
    SupportRequestResponse,
)


ALLOWED_STATUSES = {
    "pending",
    "accepted",
    "rejected",
    "escalated",
    "resolved",
    "cancelled",
}


class SupportRequestNotFoundError(Exception):
    """Raised when a request, Agent, or provider is missing."""


class SupportRequestValidationError(Exception):
    """Raised when support-request data is invalid."""


class InvalidSupportRequestTransitionError(Exception):
    """Raised when a workflow transition is not allowed."""


def current_time() -> datetime:
    """Return the current UTC datetime."""

    return datetime.now(UTC)


def add_event(
    *,
    db: Session,
    support_request: SupportRequest,
    event_type: str,
    actor_code: str,
    actor_role: str,
    from_status: str | None,
    to_status: str | None,
    note: str | None,
) -> SupportRequestEvent:
    """Append one event to a support-request timeline."""

    event = SupportRequestEvent(
        support_request_id=support_request.id,
        event_type=event_type,
        actor_code=actor_code,
        actor_role=actor_role,
        from_status=from_status,
        to_status=to_status,
        note=note,
        created_at=current_time(),
    )

    db.add(event)

    return event


def get_agent_by_code(
    db: Session,
    agent_code: str,
) -> Agent:
    """Return an Agent by code."""

    agent = db.scalar(
        select(Agent).where(
            Agent.code == agent_code
        )
    )

    if agent is None:
        raise SupportRequestNotFoundError(
            f"Agent '{agent_code}' was not found."
        )

    return agent


def get_provider_by_code(
    db: Session,
    provider_code: str,
) -> Provider:
    """Return a provider by code."""

    provider = db.scalar(
        select(Provider).where(
            Provider.code == provider_code
        )
    )

    if provider is None:
        raise SupportRequestNotFoundError(
            f"Provider '{provider_code}' was not found."
        )

    return provider


def get_support_request_model(
    db: Session,
    support_request_id: int,
) -> SupportRequest:
    """Return one stored support request."""

    support_request = db.get(
        SupportRequest,
        support_request_id,
    )

    if support_request is None:
        raise SupportRequestNotFoundError(
            "Support request "
            f"'{support_request_id}' was not found."
        )

    return support_request


def resource_type_for_transaction(
    transaction_type: str,
) -> str:
    """Return the resource needed for the transaction."""

    if transaction_type == "cash_in":
        return "provider_float"

    return "physical_cash"


def build_response(
    db: Session,
    support_request: SupportRequest,
) -> SupportRequestResponse:
    """Build one API response with its full timeline."""

    requesting_agent = db.get(
        Agent,
        support_request.requesting_agent_id,
    )
    supporting_agent = db.get(
        Agent,
        support_request.supporting_agent_id,
    )
    provider = db.get(
        Provider,
        support_request.provider_id,
    )

    if (
        requesting_agent is None
        or supporting_agent is None
        or provider is None
    ):
        raise SupportRequestValidationError(
            "Stored support-request references are incomplete."
        )

    event_models = db.scalars(
        select(SupportRequestEvent)
        .where(
            SupportRequestEvent.support_request_id
            == support_request.id
        )
        .order_by(
            SupportRequestEvent.created_at,
            SupportRequestEvent.id,
        )
    ).all()

    events = [
        SupportRequestEventResponse(
            id=event.id,
            event_type=event.event_type,
            actor_code=event.actor_code,
            actor_role=event.actor_role,
            from_status=event.from_status,
            to_status=event.to_status,
            note=event.note,
            created_at=event.created_at,
        )
        for event in event_models
    ]

    return SupportRequestResponse(
        id=support_request.id,
        requesting_agent_code=requesting_agent.code,
        supporting_agent_code=supporting_agent.code,
        provider_code=provider.code,
        transaction_type=support_request.transaction_type,
        resource_type=support_request.resource_type,
        requested_amount=Decimal(
            support_request.requested_amount
        ),
        approved_amount=(
            Decimal(support_request.approved_amount)
            if support_request.approved_amount is not None
            else None
        ),
        status=support_request.status,
        reason=support_request.reason,
        created_by=support_request.created_by,
        operations_owner=support_request.operations_owner,
        created_at=support_request.created_at,
        updated_at=support_request.updated_at,
        events=events,
    )


def create_support_request(
    db: Session,
    payload: SupportRequestCreate,
) -> SupportRequestResponse:
    """Create a new pending Agent-to-Agent support request."""

    if (
        payload.requesting_agent_code
        == payload.supporting_agent_code
    ):
        raise SupportRequestValidationError(
            "The requesting and supporting Agents must be different."
        )

    requesting_agent = get_agent_by_code(
        db,
        payload.requesting_agent_code,
    )
    supporting_agent = get_agent_by_code(
        db,
        payload.supporting_agent_code,
    )
    provider = get_provider_by_code(
        db,
        payload.provider_code,
    )

    if not requesting_agent.is_active:
        raise SupportRequestValidationError(
            "The requesting Agent is inactive."
        )

    if not supporting_agent.is_active:
        raise SupportRequestValidationError(
            "The supporting Agent is inactive."
        )

    now = current_time()

    support_request = SupportRequest(
        requesting_agent_id=requesting_agent.id,
        supporting_agent_id=supporting_agent.id,
        provider_id=provider.id,
        transaction_type=payload.transaction_type,
        resource_type=resource_type_for_transaction(
            payload.transaction_type
        ),
        requested_amount=payload.requested_amount,
        approved_amount=None,
        status="pending",
        reason=payload.reason,
        created_by=payload.created_by,
        operations_owner=payload.operations_owner,
        created_at=now,
        updated_at=now,
    )

    try:
        db.add(support_request)
        db.flush()

        add_event(
            db=db,
            support_request=support_request,
            event_type="created",
            actor_code=payload.created_by,
            actor_role="requesting_agent",
            from_status=None,
            to_status="pending",
            note=payload.reason,
        )

        db.commit()
        db.refresh(support_request)

    except Exception:
        db.rollback()
        raise

    return build_response(
        db,
        support_request,
    )


def list_support_requests(
    db: Session,
    status_filter: str | None,
) -> SupportRequestListResponse:
    """List support requests for Operations monitoring."""

    if (
        status_filter is not None
        and status_filter not in ALLOWED_STATUSES
    ):
        raise SupportRequestValidationError(
            f"Unsupported status filter: {status_filter}"
        )

    statement = select(
        SupportRequest
    ).order_by(
        SupportRequest.created_at.desc(),
        SupportRequest.id.desc(),
    )

    if status_filter is not None:
        statement = statement.where(
            SupportRequest.status
            == status_filter
        )

    models = db.scalars(statement).all()

    items = [
        build_response(
            db,
            support_request,
        )
        for support_request in models
    ]

    return SupportRequestListResponse(
        total=len(items),
        items=items,
    )


def get_support_request(
    db: Session,
    support_request_id: int,
) -> SupportRequestResponse:
    """Return one request with its complete timeline."""

    support_request = get_support_request_model(
        db,
        support_request_id,
    )

    return build_response(
        db,
        support_request,
    )


def accept_support_request(
    db: Session,
    support_request_id: int,
    payload: AcceptSupportRequest,
) -> SupportRequestResponse:
    """Allow the supporting Agent to accept a request."""

    support_request = get_support_request_model(
        db,
        support_request_id,
    )

    if support_request.status != "pending":
        raise InvalidSupportRequestTransitionError(
            "Only a pending support request can be accepted."
        )

    approved_amount = (
        payload.approved_amount
        if payload.approved_amount is not None
        else Decimal(support_request.requested_amount)
    )

    if approved_amount > support_request.requested_amount:
        raise SupportRequestValidationError(
            "Approved amount cannot exceed requested amount."
        )

    previous_status = support_request.status

    try:
        support_request.status = "accepted"
        support_request.approved_amount = approved_amount
        support_request.updated_at = current_time()

        add_event(
            db=db,
            support_request=support_request,
            event_type="accepted",
            actor_code=payload.actor_code,
            actor_role="supporting_agent",
            from_status=previous_status,
            to_status="accepted",
            note=payload.note,
        )

        db.commit()
        db.refresh(support_request)

    except Exception:
        db.rollback()
        raise

    return build_response(
        db,
        support_request,
    )


def reject_support_request(
    db: Session,
    support_request_id: int,
    payload: SupportRequestAction,
) -> SupportRequestResponse:
    """Allow the supporting Agent to reject a pending request."""

    support_request = get_support_request_model(
        db,
        support_request_id,
    )

    if support_request.status != "pending":
        raise InvalidSupportRequestTransitionError(
            "Only a pending support request can be rejected."
        )

    previous_status = support_request.status

    try:
        support_request.status = "rejected"
        support_request.updated_at = current_time()

        add_event(
            db=db,
            support_request=support_request,
            event_type="rejected",
            actor_code=payload.actor_code,
            actor_role="supporting_agent",
            from_status=previous_status,
            to_status="rejected",
            note=payload.note,
        )

        db.commit()
        db.refresh(support_request)

    except Exception:
        db.rollback()
        raise

    return build_response(
        db,
        support_request,
    )


def escalate_support_request(
    db: Session,
    support_request_id: int,
    payload: SupportRequestAction,
) -> SupportRequestResponse:
    """Escalate a pending or accepted request to Operations."""

    support_request = get_support_request_model(
        db,
        support_request_id,
    )

    if support_request.status not in {
        "pending",
        "accepted",
    }:
        raise InvalidSupportRequestTransitionError(
            "Only a pending or accepted request can be escalated."
        )

    previous_status = support_request.status

    try:
        support_request.status = "escalated"
        support_request.updated_at = current_time()

        add_event(
            db=db,
            support_request=support_request,
            event_type="escalated",
            actor_code=payload.actor_code,
            actor_role="operations",
            from_status=previous_status,
            to_status="escalated",
            note=payload.note,
        )

        db.commit()
        db.refresh(support_request)

    except Exception:
        db.rollback()
        raise

    return build_response(
        db,
        support_request,
    )


def resolve_support_request(
    db: Session,
    support_request_id: int,
    payload: SupportRequestAction,
) -> SupportRequestResponse:
    """Resolve an accepted or escalated support request."""

    support_request = get_support_request_model(
        db,
        support_request_id,
    )

    if support_request.status not in {
        "accepted",
        "escalated",
    }:
        raise InvalidSupportRequestTransitionError(
            "Only an accepted or escalated request can be resolved."
        )

    previous_status = support_request.status

    try:
        support_request.status = "resolved"
        support_request.updated_at = current_time()

        add_event(
            db=db,
            support_request=support_request,
            event_type="resolved",
            actor_code=payload.actor_code,
            actor_role="operations",
            from_status=previous_status,
            to_status="resolved",
            note=payload.note,
        )

        db.commit()
        db.refresh(support_request)

    except Exception:
        db.rollback()
        raise

    return build_response(
        db,
        support_request,
    )


def add_support_request_note(
    db: Session,
    support_request_id: int,
    payload: SupportRequestNoteCreate,
) -> SupportRequestResponse:
    """Add a timeline note without changing workflow status."""

    support_request = get_support_request_model(
        db,
        support_request_id,
    )

    try:
        add_event(
            db=db,
            support_request=support_request,
            event_type="note_added",
            actor_code=payload.actor_code,
            actor_role=payload.actor_role,
            from_status=support_request.status,
            to_status=support_request.status,
            note=payload.note,
        )

        support_request.updated_at = current_time()

        db.commit()
        db.refresh(support_request)

    except Exception:
        db.rollback()
        raise

    return build_response(
        db,
        support_request,
    )