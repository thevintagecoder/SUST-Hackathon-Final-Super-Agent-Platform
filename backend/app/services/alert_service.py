"""Read persisted alerts and their review timelines."""

from __future__ import annotations

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import (
    Session,
    selectinload,
)

from backend.app.models import (
    Agent,
    Alert,
    Provider,
)
from backend.app.schemas.alert import (
    AlertDetailResponse,
    AlertEventResponse,
    AlertListResponse,
    AlertStatus,
    AlertSummaryResponse,
    AlertType,
    LocalizedAlertText,
)


class AlertNotFoundError(Exception):
    """Raised when a persisted alert cannot be found."""


def build_title(
    alert: Alert,
) -> LocalizedAlertText:
    """Build localized alert titles."""

    return LocalizedAlertText(
        en=alert.title_en,
        bn=alert.title_bn,
        bn_latn=alert.title_bn_latn,
    )


def build_message(
    alert: Alert,
) -> LocalizedAlertText:
    """Build localized alert messages."""

    return LocalizedAlertText(
        en=alert.message_en,
        bn=alert.message_bn,
        bn_latn=alert.message_bn_latn,
    )


def build_next_step(
    alert: Alert,
) -> LocalizedAlertText:
    """Build localized recommended next steps."""

    return LocalizedAlertText(
        en=alert.next_step_en,
        bn=alert.next_step_bn,
        bn_latn=alert.next_step_bn_latn,
    )


def build_alert_summary(
    *,
    alert: Alert,
    agent_code: str,
    provider_code: str | None,
) -> AlertSummaryResponse:
    """Convert a database alert into a list response."""

    return AlertSummaryResponse(
        id=alert.id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        status=alert.status,
        agent_code=agent_code,
        provider_code=provider_code,
        scenario_id=alert.scenario_id,
        title=build_title(
            alert
        ),
        confidence=alert.confidence,
        freshness_state=(
            alert.freshness_state
        ),
        human_review_required=(
            alert.human_review_required
        ),
        automatic_action_taken=(
            alert.automatic_action_taken
        ),
        assigned_to=alert.assigned_to,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


def build_alert_detail(
    *,
    alert: Alert,
    agent_code: str,
    provider_code: str | None,
) -> AlertDetailResponse:
    """Convert a database alert into a detail response."""

    summary = build_alert_summary(
        alert=alert,
        agent_code=agent_code,
        provider_code=provider_code,
    )

    events = [
        AlertEventResponse(
            id=event.id,
            event_type=event.event_type,
            actor=event.actor,
            note=event.note,
            event_data=dict(
                event.event_data or {}
            ),
            created_at=event.created_at,
        )
        for event in alert.events
    ]

    return AlertDetailResponse(
        **summary.model_dump(),
        source_reference=(
            alert.source_reference
        ),
        message=build_message(
            alert
        ),
        next_step=build_next_step(
            alert
        ),
        evidence=dict(
            alert.evidence or {}
        ),
        acknowledged_at=(
            alert.acknowledged_at
        ),
        resolved_at=alert.resolved_at,
        events=events,
    )


def build_alert_filters(
    *,
    status_filter: AlertStatus | None,
    alert_type: AlertType | None,
    agent_code: str | None,
    provider_code: str | None,
    scenario_id: str | None,
) -> list[object]:
    """Build optional filters for alert list queries."""

    filters: list[object] = []

    if status_filter is not None:
        filters.append(
            Alert.status == status_filter
        )

    if alert_type is not None:
        filters.append(
            Alert.alert_type == alert_type
        )

    if agent_code is not None:
        filters.append(
            Agent.code == agent_code
        )

    if provider_code is not None:
        filters.append(
            Provider.code == provider_code
        )

    if scenario_id is not None:
        filters.append(
            Alert.scenario_id == scenario_id
        )

    return filters


def list_alerts(
    *,
    db: Session,
    status_filter: AlertStatus | None = None,
    alert_type: AlertType | None = None,
    agent_code: str | None = None,
    provider_code: str | None = None,
    scenario_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> AlertListResponse:
    """Return filtered persisted alerts."""

    filters = build_alert_filters(
        status_filter=status_filter,
        alert_type=alert_type,
        agent_code=agent_code,
        provider_code=provider_code,
        scenario_id=scenario_id,
    )

    statement = (
        select(
            Alert,
            Agent.code,
            Provider.code,
        )
        .join(
            Agent,
            Alert.agent_id == Agent.id,
        )
        .outerjoin(
            Provider,
            Alert.provider_id == Provider.id,
        )
        .where(
            *filters
        )
        .order_by(
            Alert.created_at.desc(),
            Alert.id.desc(),
        )
        .limit(
            limit
        )
        .offset(
            offset
        )
    )

    rows = db.execute(
        statement
    ).all()

    count_statement = (
        select(
            func.count(
                Alert.id
            )
        )
        .join(
            Agent,
            Alert.agent_id == Agent.id,
        )
        .outerjoin(
            Provider,
            Alert.provider_id == Provider.id,
        )
        .where(
            *filters
        )
    )

    total = db.scalar(
        count_statement
    )

    items = [
        build_alert_summary(
            alert=alert,
            agent_code=row_agent_code,
            provider_code=(
                row_provider_code
            ),
        )
        for (
            alert,
            row_agent_code,
            row_provider_code,
        ) in rows
    ]

    return AlertListResponse(
        items=items,
        total=int(
            total or 0
        ),
        limit=limit,
        offset=offset,
    )


def get_alert_detail(
    *,
    db: Session,
    alert_id: int,
) -> AlertDetailResponse:
    """Return one alert with its event timeline."""

    statement = (
        select(
            Alert,
            Agent.code,
            Provider.code,
        )
        .join(
            Agent,
            Alert.agent_id == Agent.id,
        )
        .outerjoin(
            Provider,
            Alert.provider_id == Provider.id,
        )
        .options(
            selectinload(
                Alert.events
            )
        )
        .where(
            Alert.id == alert_id
        )
    )

    row = db.execute(
        statement
    ).one_or_none()

    if row is None:
        raise AlertNotFoundError(
            f"Alert '{alert_id}' was not found."
        )

    alert, agent_code, provider_code = row

    return build_alert_detail(
        alert=alert,
        agent_code=agent_code,
        provider_code=provider_code,
    )