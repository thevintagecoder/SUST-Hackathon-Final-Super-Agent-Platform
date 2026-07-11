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