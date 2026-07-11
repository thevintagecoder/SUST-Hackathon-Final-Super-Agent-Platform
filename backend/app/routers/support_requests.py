"""FastAPI routes for Agent-to-Agent support-request workflows."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.support_request import (
    AcceptSupportRequest,
    SupportRequestAction,
    SupportRequestCreate,
    SupportRequestListResponse,
    SupportRequestNoteCreate,
    SupportRequestResponse,
)
from backend.app.services.support_request_service import (
    InvalidSupportRequestTransitionError,
    SupportRequestNotFoundError,
    SupportRequestValidationError,
    accept_support_request,
    add_support_request_note,
    create_support_request,
    escalate_support_request,
    get_support_request,
    list_support_requests,
    reject_support_request,
    resolve_support_request,
)


router = APIRouter(
    prefix="/support-requests",
    tags=["Support Requests"],
)


def convert_workflow_error(
    exc: Exception,
) -> HTTPException:
    """Convert service exceptions into API errors."""

    if isinstance(
        exc,
        SupportRequestNotFoundError,
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(
        exc,
        InvalidSupportRequestTransitionError,
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


@router.post(
    "",
    response_model=SupportRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_request(
    payload: SupportRequestCreate,
    db: Session = Depends(get_db),
) -> SupportRequestResponse:
    """Create a pending support request."""

    try:
        return create_support_request(
            db,
            payload,
        )
    except (
        SupportRequestNotFoundError,
        SupportRequestValidationError,
    ) as exc:
        raise convert_workflow_error(
            exc
        ) from exc


@router.get(
    "",
    response_model=SupportRequestListResponse,
)
def list_requests(
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    db: Session = Depends(get_db),
) -> SupportRequestListResponse:
    """List support requests for Operations monitoring."""

    try:
        return list_support_requests(
            db,
            status_filter,
        )
    except SupportRequestValidationError as exc:
        raise convert_workflow_error(
            exc
        ) from exc


@router.get(
    "/{support_request_id}",
    response_model=SupportRequestResponse,
)
def read_request(
    support_request_id: int,
    db: Session = Depends(get_db),
) -> SupportRequestResponse:
    """Read one support request and its timeline."""

    try:
        return get_support_request(
            db,
            support_request_id,
        )
    except SupportRequestNotFoundError as exc:
        raise convert_workflow_error(
            exc
        ) from exc


@router.post(
    "/{support_request_id}/accept",
    response_model=SupportRequestResponse,
)
def accept_request(
    support_request_id: int,
    payload: AcceptSupportRequest,
    db: Session = Depends(get_db),
) -> SupportRequestResponse:
    """Accept all or part of a support request."""

    try:
        return accept_support_request(
            db,
            support_request_id,
            payload,
        )
    except (
        SupportRequestNotFoundError,
        SupportRequestValidationError,
        InvalidSupportRequestTransitionError,
    ) as exc:
        raise convert_workflow_error(
            exc
        ) from exc


@router.post(
    "/{support_request_id}/reject",
    response_model=SupportRequestResponse,
)
def reject_request(
    support_request_id: int,
    payload: SupportRequestAction,
    db: Session = Depends(get_db),
) -> SupportRequestResponse:
    """Reject a pending support request."""

    try:
        return reject_support_request(
            db,
            support_request_id,
            payload,
        )
    except (
        SupportRequestNotFoundError,
        InvalidSupportRequestTransitionError,
    ) as exc:
        raise convert_workflow_error(
            exc
        ) from exc


@router.post(
    "/{support_request_id}/escalate",
    response_model=SupportRequestResponse,
)
def escalate_request(
    support_request_id: int,
    payload: SupportRequestAction,
    db: Session = Depends(get_db),
) -> SupportRequestResponse:
    """Escalate a request to Operations."""

    try:
        return escalate_support_request(
            db,
            support_request_id,
            payload,
        )
    except (
        SupportRequestNotFoundError,
        InvalidSupportRequestTransitionError,
    ) as exc:
        raise convert_workflow_error(
            exc
        ) from exc


@router.post(
    "/{support_request_id}/resolve",
    response_model=SupportRequestResponse,
)
def resolve_request(
    support_request_id: int,
    payload: SupportRequestAction,
    db: Session = Depends(get_db),
) -> SupportRequestResponse:
    """Resolve an accepted or escalated request."""

    try:
        return resolve_support_request(
            db,
            support_request_id,
            payload,
        )
    except (
        SupportRequestNotFoundError,
        InvalidSupportRequestTransitionError,
    ) as exc:
        raise convert_workflow_error(
            exc
        ) from exc


@router.post(
    "/{support_request_id}/notes",
    response_model=SupportRequestResponse,
)
def add_request_note(
    support_request_id: int,
    payload: SupportRequestNoteCreate,
    db: Session = Depends(get_db),
) -> SupportRequestResponse:
    """Add an append-only note to the timeline."""

    try:
        return add_support_request_note(
            db,
            support_request_id,
            payload,
        )
    except SupportRequestNotFoundError as exc:
        raise convert_workflow_error(
            exc
        ) from exc