"""Aggregate Agent liquidity and alert intelligence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import (
    Agent,
    AgentPosition,
    Alert,
    Provider,
    ProviderBalance,
)
from backend.app.schemas.alert import (
    LocalizedAlertText,
)
from backend.app.schemas.dashboard import (
    AgentDashboardResponse,
    AgentIdentityResponse,
    AgentRiskSummary,
    DashboardAlertItem,
    ProviderBalanceCard,
    SharedCashCard,
    OperationsAgentRiskRow,
    OperationsAlertItem,
    OperationsDashboardResponse,
    OperationsSummaryResponse,
)


SEVERITY_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


class DashboardNotFoundError(Exception):
    """Raised when a dashboard resource cannot be found."""


def provider_display_name(
    provider: Provider,
) -> str:
    """Return a human-readable provider name."""

    provider_name = getattr(
        provider,
        "name",
        None,
    )

    if (
        isinstance(provider_name, str)
        and provider_name.strip()
    ):
        return provider_name.strip()

    return provider.code


def build_alert_title(
    alert: Alert,
) -> LocalizedAlertText:
    """Return an alert title in every supported language."""

    return LocalizedAlertText(
        en=alert.title_en,
        bn=alert.title_bn,
        bn_latn=alert.title_bn_latn,
    )


def find_agent(
    *,
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
        raise DashboardNotFoundError(
            f"Agent '{agent_code}' was not found."
        )

    return agent


def get_shared_cash_card(
    *,
    db: Session,
    agent: Agent,
) -> SharedCashCard:
    """Return the Agent's physical-cash dashboard card."""

    position = db.scalar(
        select(AgentPosition).where(
            AgentPosition.agent_id == agent.id
        )
    )

    if position is None:
        return SharedCashCard(
            available=False,
            balance=None,
            as_of=None,
        )

    return SharedCashCard(
        available=True,
        balance=position.shared_cash,
        as_of=position.as_of,
    )


def get_provider_balance_cards(
    *,
    db: Session,
    agent: Agent,
) -> list[ProviderBalanceCard]:
    """Return provider-specific electronic-float cards."""

    statement = (
        select(
            ProviderBalance,
            Provider,
        )
        .join(
            Provider,
            ProviderBalance.provider_id
            == Provider.id,
        )
        .where(
            ProviderBalance.agent_id
            == agent.id
        )
        .order_by(
            Provider.code
        )
    )

    rows = db.execute(
        statement
    ).all()

    return [
        ProviderBalanceCard(
            provider_code=provider.code,
            provider_name=(
                provider_display_name(
                    provider
                )
            ),
            electronic_balance=(
                balance.electronic_balance
            ),
            freshness_state=(
                balance.freshness_state
            ),
            last_update_at=(
                balance.last_update_at
            ),
        )
        for balance, provider in rows
    ]


def get_active_alerts(
    *,
    db: Session,
    agent: Agent,
    scenario_id: str | None,
) -> list[Alert]:
    """Return unresolved alerts for one Agent."""

    statement = (
        select(Alert)
        .where(
            Alert.agent_id == agent.id,
            Alert.status != "RESOLVED",
        )
        .order_by(
            Alert.created_at.desc(),
            Alert.id.desc(),
        )
    )

    if scenario_id is not None:
        statement = statement.where(
            Alert.scenario_id == scenario_id
        )

    return list(
        db.scalars(
            statement
        ).all()
    )


def highest_severity(
    alerts: list[Alert],
) -> str | None:
    """Return the highest severity among active alerts."""

    if not alerts:
        return None

    return max(
        (
            alert.severity
            for alert in alerts
        ),
        key=lambda severity: (
            SEVERITY_ORDER.get(
                severity,
                0,
            )
        ),
    )


def build_severity_counts(
    alerts: list[Alert],
) -> dict[str, int]:
    """Count active alerts by severity."""

    counts = {
        "LOW": 0,
        "MEDIUM": 0,
        "HIGH": 0,
        "CRITICAL": 0,
    }

    for alert in alerts:
        if alert.severity in counts:
            counts[alert.severity] += 1

    return counts


def build_alert_type_counts(
    alerts: list[Alert],
) -> dict[str, int]:
    """Count active alerts by alert type."""

    counts = {
        "LIQUIDITY_RUNWAY": 0,
        "ANOMALY_REVIEW": 0,
        "STALE_DATA": 0,
        "SERVICEABILITY_SHORTFALL": 0,
    }

    for alert in alerts:
        if alert.alert_type in counts:
            counts[alert.alert_type] += 1

    return counts


def build_dashboard_alert_item(
    *,
    alert: Alert,
    provider_code: str | None,
) -> DashboardAlertItem:
    """Convert one alert into a dashboard card."""

    return DashboardAlertItem(
        id=alert.id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        status=alert.status,
        provider_code=provider_code,
        scenario_id=alert.scenario_id,
        title=build_alert_title(
            alert
        ),
        confidence=alert.confidence,
        freshness_state=(
            alert.freshness_state
        ),
        assigned_to=alert.assigned_to,
        created_at=alert.created_at,
        human_review_required=(
            alert.human_review_required
        ),
        automatic_action_taken=(
            alert.automatic_action_taken
        ),
    )


def get_provider_codes_for_alerts(
    *,
    db: Session,
    alerts: list[Alert],
) -> dict[int, str]:
    """Map provider identifiers to provider codes."""

    provider_ids = {
        alert.provider_id
        for alert in alerts
        if alert.provider_id is not None
    }

    if not provider_ids:
        return {}

    statement = select(
        Provider.id,
        Provider.code,
    ).where(
        Provider.id.in_(
            provider_ids
        )
    )

    return {
        provider_id: provider_code
        for provider_id, provider_code
        in db.execute(statement).all()
    }


def get_agent_dashboard(
    *,
    db: Session,
    agent_code: str,
    scenario_id: str | None = None,
    recent_alert_limit: int = 5,
) -> AgentDashboardResponse:
    """Build one Agent/Super Agent dashboard."""

    agent = find_agent(
        db=db,
        agent_code=agent_code,
    )

    shared_cash = get_shared_cash_card(
        db=db,
        agent=agent,
    )

    provider_balances = (
        get_provider_balance_cards(
            db=db,
            agent=agent,
        )
    )

    active_alerts = get_active_alerts(
        db=db,
        agent=agent,
        scenario_id=scenario_id,
    )

    provider_codes = (
        get_provider_codes_for_alerts(
            db=db,
            alerts=active_alerts,
        )
    )

    recent_alerts = [
        build_dashboard_alert_item(
            alert=alert,
            provider_code=(
                provider_codes.get(
                    alert.provider_id
                )
                if alert.provider_id
                is not None
                else None
            ),
        )
        for alert in active_alerts[
            :recent_alert_limit
        ]
    ]

    review_required = any(
        alert.human_review_required
        for alert in active_alerts
    )

    return AgentDashboardResponse(
        agent=AgentIdentityResponse(
            code=agent.code,
            name=agent.name,
            area=agent.area,
            latitude=(
                float(agent.latitude)
                if agent.latitude
                is not None
                else None
            ),
            longitude=(
                float(agent.longitude)
                if agent.longitude
                is not None
                else None
            ),
            is_active=agent.is_active,
        ),
        shared_cash=shared_cash,
        provider_balances=(
            provider_balances
        ),
        risk_summary=AgentRiskSummary(
            active_alert_count=(
                len(active_alerts)
            ),
            highest_active_severity=(
                highest_severity(
                    active_alerts
                )
            ),
            severity_counts=(
                build_severity_counts(
                    active_alerts
                )
            ),
            alert_type_counts=(
                build_alert_type_counts(
                    active_alerts
                )
            ),
            human_review_required=(
                review_required
            ),
            automatic_action_taken=False,
        ),
        recent_alerts=recent_alerts,
        scenario_id=scenario_id,
        generated_at=datetime.now(
            UTC
        ),
    )

def normalize_dashboard_datetime(
    value: datetime,
) -> datetime:
    """Return a timezone-aware UTC datetime."""

    if value.tzinfo is None:
        return value.replace(
            tzinfo=UTC,
        )

    return value.astimezone(
        UTC,
    )


def get_operations_dashboard(
    *,
    db: Session,
    scenario_id: str | None = None,
    recent_alert_limit: int = 10,
) -> OperationsDashboardResponse:
    """Build a cross-Agent operational overview."""

    agents = list(
        db.scalars(
            select(Agent).order_by(
                Agent.code
            )
        ).all()
    )

    agent_ids = [
        agent.id
        for agent in agents
    ]

    positions: list[AgentPosition] = []
    provider_balances: list[
        ProviderBalance
    ] = []

    if agent_ids:
        positions = list(
            db.scalars(
                select(AgentPosition).where(
                    AgentPosition.agent_id.in_(
                        agent_ids
                    )
                )
            ).all()
        )

        provider_balances = list(
            db.scalars(
                select(ProviderBalance).where(
                    ProviderBalance.agent_id.in_(
                        agent_ids
                    )
                )
            ).all()
        )

    alert_statement = (
        select(Alert)
        .where(
            Alert.status != "RESOLVED"
        )
        .order_by(
            Alert.created_at.desc(),
            Alert.id.desc(),
        )
    )

    if scenario_id is not None:
        alert_statement = (
            alert_statement.where(
                Alert.scenario_id
                == scenario_id
            )
        )

    active_alerts = list(
        db.scalars(
            alert_statement
        ).all()
    )

    positions_by_agent = {
        position.agent_id: position
        for position in positions
    }

    balances_by_agent: dict[
        int,
        list[ProviderBalance],
    ] = {}

    for balance in provider_balances:
        balances_by_agent.setdefault(
            balance.agent_id,
            [],
        ).append(
            balance
        )

    alerts_by_agent: dict[
        int,
        list[Alert],
    ] = {}

    for alert in active_alerts:
        alerts_by_agent.setdefault(
            alert.agent_id,
            [],
        ).append(
            alert
        )

    provider_ids = {
        alert.provider_id
        for alert in active_alerts
        if alert.provider_id is not None
    }

    provider_codes: dict[int, str] = {}

    if provider_ids:
        provider_codes = {
            provider_id: provider_code
            for provider_id, provider_code
            in db.execute(
                select(
                    Provider.id,
                    Provider.code,
                ).where(
                    Provider.id.in_(
                        provider_ids
                    )
                )
            ).all()
        }

    agent_codes = {
        agent.id: agent.code
        for agent in agents
    }

    agent_risks: list[
        OperationsAgentRiskRow
    ] = []

    for agent in agents:
        position = positions_by_agent.get(
            agent.id
        )

        agent_balances = (
            balances_by_agent.get(
                agent.id,
                [],
            )
        )

        agent_alerts = (
            alerts_by_agent.get(
                agent.id,
                [],
            )
        )

        stale_provider_count = sum(
            (
                balance.freshness_state
                or "missing"
            )
            != "fresh"
            for balance in agent_balances
        )

        agent_risks.append(
            OperationsAgentRiskRow(
                agent_code=agent.code,
                agent_name=agent.name,
                area=agent.area,
                is_active=agent.is_active,
                shared_cash=(
                    position.shared_cash
                    if position is not None
                    else None
                ),
                shared_cash_as_of=(
                    position.as_of
                    if position is not None
                    else None
                ),
                stale_provider_count=(
                    stale_provider_count
                ),
                active_alert_count=(
                    len(agent_alerts)
                ),
                highest_active_severity=(
                    highest_severity(
                        agent_alerts
                    )
                ),
                human_review_required=any(
                    alert
                    .human_review_required
                    for alert in agent_alerts
                ),
            )
        )

    agent_risks.sort(
        key=lambda row: (
            -SEVERITY_ORDER.get(
                row.highest_active_severity
                or "",
                0,
            ),
            -row.active_alert_count,
            row.agent_code,
        )
    )

    recent_alerts = [
        OperationsAlertItem(
            id=alert.id,
            agent_code=agent_codes[
                alert.agent_id
            ],
            provider_code=(
                provider_codes.get(
                    alert.provider_id
                )
                if alert.provider_id
                is not None
                else None
            ),
            alert_type=alert.alert_type,
            severity=alert.severity,
            status=alert.status,
            scenario_id=alert.scenario_id,
            title=build_alert_title(
                alert
            ),
            confidence=alert.confidence,
            freshness_state=(
                alert.freshness_state
            ),
            assigned_to=alert.assigned_to,
            created_at=alert.created_at,
            human_review_required=(
                alert.human_review_required
            ),
            automatic_action_taken=(
                alert.automatic_action_taken
            ),
        )
        for alert in active_alerts[
            :recent_alert_limit
        ]
    ]

    stale_provider_balance_count = sum(
        (
            balance.freshness_state
            or "missing"
        )
        != "fresh"
        for balance in provider_balances
    )

    update_candidates = [
        normalize_dashboard_datetime(
            position.as_of
        )
        for position in positions
    ]

    update_candidates.extend(
        normalize_dashboard_datetime(
            balance.last_update_at
        )
        for balance in provider_balances
    )

    update_candidates.extend(
        normalize_dashboard_datetime(
            alert.updated_at
        )
        for alert in active_alerts
    )

    last_updated_at = (
        max(
            update_candidates
        )
        if update_candidates
        else None
    )

    return OperationsDashboardResponse(
        summary=OperationsSummaryResponse(
            total_agents=len(
                agents
            ),
            active_agents=sum(
                agent.is_active
                for agent in agents
            ),
            provider_balance_count=len(
                provider_balances
            ),
            stale_provider_balance_count=(
                stale_provider_balance_count
            ),
            active_alert_count=len(
                active_alerts
            ),
            open_alert_count=sum(
                alert.status == "OPEN"
                for alert in active_alerts
            ),
            escalated_alert_count=sum(
                alert.status == "ESCALATED"
                for alert in active_alerts
            ),
            unassigned_alert_count=sum(
                alert.assigned_to is None
                for alert in active_alerts
            ),
            high_or_critical_alert_count=sum(
                alert.severity
                in {
                    "HIGH",
                    "CRITICAL",
                }
                for alert in active_alerts
            ),
            human_review_required_count=sum(
                alert.human_review_required
                for alert in active_alerts
            ),
            severity_counts=(
                build_severity_counts(
                    active_alerts
                )
            ),
            alert_type_counts=(
                build_alert_type_counts(
                    active_alerts
                )
            ),
            automatic_action_taken=False,
        ),
        agent_risks=agent_risks,
        recent_alerts=recent_alerts,
        scenario_id=scenario_id,
        last_updated_at=last_updated_at,
        generated_at=datetime.now(
            UTC
        ),
        synthetic_data_notice=(
            "Synthetic demonstration data only. "
            "Human review is required before any "
            "operational decision."
        ),
    )