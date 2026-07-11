"""Schemas for stakeholder intelligence dashboards."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from backend.app.schemas.alert import (
    AlertSeverity,
    AlertStatus,
    AlertType,
    LocalizedAlertText,
)


class AgentIdentityResponse(BaseModel):
    """Return the Agent identity displayed on the dashboard."""

    code: str
    name: str
    area: str

    latitude: float | None
    longitude: float | None

    is_active: bool


class SharedCashCard(BaseModel):
    """Return the Agent's shared physical-cash position."""

    available: bool
    balance: Decimal | None
    as_of: datetime | None


class ProviderBalanceCard(BaseModel):
    """Return one provider-specific electronic-float position."""

    provider_code: str
    provider_name: str

    electronic_balance: Decimal
    freshness_state: str
    last_update_at: datetime


class DashboardAlertItem(BaseModel):
    """Return one unresolved alert for dashboard display."""

    id: int
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus

    provider_code: str | None
    scenario_id: str | None

    title: LocalizedAlertText

    confidence: Decimal
    freshness_state: str | None

    assigned_to: str | None
    created_at: datetime

    human_review_required: bool
    automatic_action_taken: bool


class AgentRiskSummary(BaseModel):
    """Summarize active Agent risks and review requirements."""

    active_alert_count: int

    highest_active_severity: AlertSeverity | None

    severity_counts: dict[str, int]
    alert_type_counts: dict[str, int]

    human_review_required: bool
    automatic_action_taken: bool = False


class AgentDashboardResponse(BaseModel):
    """Return the Agent/Super Agent intelligence dashboard."""

    agent: AgentIdentityResponse

    shared_cash: SharedCashCard

    provider_balances: list[
        ProviderBalanceCard
    ]

    risk_summary: AgentRiskSummary

    recent_alerts: list[
        DashboardAlertItem
    ]

    scenario_id: str | None

    generated_at: datetime


class OperationsSummaryResponse(BaseModel):
    """Summarize current operational workload."""

    total_agents: int
    active_agents: int

    provider_balance_count: int
    stale_provider_balance_count: int

    active_alert_count: int
    open_alert_count: int
    escalated_alert_count: int
    unassigned_alert_count: int

    high_or_critical_alert_count: int
    human_review_required_count: int

    severity_counts: dict[str, int]
    alert_type_counts: dict[str, int]

    automatic_action_taken: bool = False


class OperationsAgentRiskRow(BaseModel):
    """Summarize operational risk for one Agent."""

    agent_code: str
    agent_name: str
    area: str
    is_active: bool

    shared_cash: Decimal | None
    shared_cash_as_of: datetime | None

    stale_provider_count: int
    active_alert_count: int

    highest_active_severity: AlertSeverity | None
    human_review_required: bool


class OperationsAlertItem(BaseModel):
    """Return one active alert for Operations."""

    id: int

    agent_code: str
    provider_code: str | None

    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus

    scenario_id: str | None
    title: LocalizedAlertText

    confidence: Decimal
    freshness_state: str | None

    assigned_to: str | None
    created_at: datetime

    human_review_required: bool
    automatic_action_taken: bool


class OperationsDashboardResponse(BaseModel):
    """Return the cross-Agent Operations dashboard."""

    summary: OperationsSummaryResponse

    agent_risks: list[
        OperationsAgentRiskRow
    ]

    recent_alerts: list[
        OperationsAlertItem
    ]

    scenario_id: str | None

    last_updated_at: datetime | None
    generated_at: datetime

    synthetic_data_notice: str


class ProviderIdentityResponse(BaseModel):
    """Return provider identity information."""

    code: str
    name: str


class ProviderDashboardSummaryResponse(BaseModel):
    """Summarize one provider's liquidity and risk state."""

    agents_with_balance: int

    total_electronic_balance: Decimal

    prototype_safety_threshold: Decimal

    at_or_below_safety_threshold_count: int

    fresh_balance_count: int
    non_fresh_balance_count: int

    active_alert_count: int
    open_alert_count: int
    escalated_alert_count: int

    high_or_critical_alert_count: int
    human_review_required_count: int

    severity_counts: dict[str, int]
    alert_type_counts: dict[str, int]

    automatic_action_taken: bool = False


class ProviderAgentBalanceRow(BaseModel):
    """Return one Agent's balance for the selected provider."""

    agent_code: str
    agent_name: str
    area: str
    is_active: bool

    electronic_balance: Decimal

    prototype_safety_threshold: Decimal

    at_or_below_safety_threshold: bool

    freshness_state: str
    last_update_at: datetime

    active_alert_count: int

    highest_active_severity: AlertSeverity | None

    human_review_required: bool


class ProviderDashboardAlertItem(BaseModel):
    """Return one provider-related active alert."""

    id: int

    agent_code: str

    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus

    scenario_id: str | None

    title: LocalizedAlertText

    confidence: Decimal
    freshness_state: str | None

    assigned_to: str | None
    created_at: datetime

    human_review_required: bool
    automatic_action_taken: bool


class ProviderDashboardResponse(BaseModel):
    """Return one provider stakeholder dashboard."""

    provider: ProviderIdentityResponse

    summary: ProviderDashboardSummaryResponse

    agent_balances: list[
        ProviderAgentBalanceRow
    ]

    recent_alerts: list[
        ProviderDashboardAlertItem
    ]

    scenario_id: str | None

    last_updated_at: datetime | None
    generated_at: datetime

    synthetic_data_notice: str