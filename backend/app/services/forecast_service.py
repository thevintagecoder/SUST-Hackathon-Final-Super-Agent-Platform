"""Explainable liquidity runway forecasting logic."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import (
    Agent,
    AgentPosition,
    Provider,
    ProviderBalance,
    Transaction,
)
from backend.app.schemas.forecast import (
    ForecastRiskLevel,
    LiquidityRunwayRequest,
    LiquidityRunwayResponse,
)
from backend.app.services.network_service import (
    PHYSICAL_CASH_SAFETY_RESERVE,
    PROVIDER_FLOAT_SAFETY_RESERVE,
)


ZERO = Decimal("0.00")
TWO_DECIMAL_PLACES = Decimal("0.01")
MINIMUM_HISTORY_COUNT = 3


class ForecastNotFoundError(Exception):
    """Raised when an Agent or provider cannot be found."""


class ForecastValidationError(Exception):
    """Raised when a forecast request is inconsistent."""


class ForecastDataUnavailableError(Exception):
    """Raised when forecast input data is unavailable."""


def as_decimal(value: object) -> Decimal:
    """Convert a database numeric value into Decimal."""

    return Decimal(str(value))


def confidence_for_forecast(
    *,
    freshness_state: str,
    sample_count: int,
) -> Decimal:
    """Calculate confidence from freshness and sample size."""

    freshness_scores = {
        "fresh": Decimal("0.95"),
        "delayed": Decimal("0.60"),
        "conflicting": Decimal("0.30"),
        "missing": Decimal("0.15"),
    }

    freshness_score = freshness_scores.get(
        freshness_state,
        Decimal("0.20"),
    )

    if sample_count >= 20:
        sample_score = Decimal("0.95")
    elif sample_count >= 10:
        sample_score = Decimal("0.85")
    elif sample_count >= 5:
        sample_score = Decimal("0.70")
    elif sample_count >= MINIMUM_HISTORY_COUNT:
        sample_score = Decimal("0.55")
    else:
        sample_score = Decimal("0.30")

    confidence = (
        freshness_score * Decimal("0.60")
        + sample_score * Decimal("0.40")
    )

    return confidence.quantize(
        TWO_DECIMAL_PLACES
    )


def calculate_resource_flows(
    *,
    transactions: list[Transaction],
    resource_type: str,
) -> tuple[Decimal, Decimal]:
    """Calculate resource consumption and replenishment."""

    gross_consumption = ZERO
    gross_replenishment = ZERO

    for transaction in transactions:
        amount = as_decimal(
            transaction.amount
        )

        if resource_type == "provider_float":
            if transaction.transaction_type == "cash_in":
                gross_consumption += amount
            else:
                gross_replenishment += amount

        else:
            if transaction.transaction_type == "cash_out":
                gross_consumption += amount
            else:
                gross_replenishment += amount

    return (
        gross_consumption,
        gross_replenishment,
    )


def calculate_risk_level(
    *,
    current_balance: Decimal,
    safety_threshold: Decimal,
    sample_count: int,
    net_consumption_per_hour: Decimal,
    runway_hours: Decimal | None,
    warning_threshold_hours: Decimal,
) -> ForecastRiskLevel:
    """Classify the forecast using transparent thresholds."""

    if current_balance <= safety_threshold:
        return "CRITICAL"

    if sample_count < MINIMUM_HISTORY_COUNT:
        return "INSUFFICIENT_HISTORY"

    if net_consumption_per_hour <= ZERO:
        return "STABLE_OR_REPLENISHING"

    if runway_hours is None:
        return "INSUFFICIENT_HISTORY"

    if runway_hours <= Decimal("2.00"):
        return "CRITICAL"

    if runway_hours <= warning_threshold_hours:
        return "HIGH"

    if runway_hours <= Decimal("24.00"):
        return "MEDIUM"

    return "LOW"


def build_warning_message(
    *,
    risk_level: ForecastRiskLevel,
    runway_hours: Decimal | None,
) -> str:
    """Create responsible warning language."""

    if risk_level == "CRITICAL":
        if runway_hours == ZERO:
            return (
                "The current balance is already at or below the "
                "prototype safety threshold. Human review is required."
            )

        return (
            "The resource may fall below the prototype safety "
            "threshold very soon if the recent net-consumption "
            "pattern continues."
        )

    if risk_level == "HIGH":
        return (
            "The resource may fall below the prototype safety "
            "threshold within the configured warning window."
        )

    if risk_level == "MEDIUM":
        return (
            "The recent pattern indicates continued depletion. "
            "Monitor the resource and prepare a human response."
        )

    if risk_level == "LOW":
        return (
            "The resource is being depleted, but the estimated "
            "runway remains above the near-term warning window."
        )

    if risk_level == "STABLE_OR_REPLENISHING":
        return (
            "The selected window does not show positive net "
            "consumption. A threshold-breach time is not estimated."
        )

    return (
        "There are too few completed transactions for a reliable "
        "runway classification. Collect more observations."
    )


def find_agent(
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
        raise ForecastNotFoundError(
            f"Agent '{agent_code}' was not found."
        )

    if not agent.is_active:
        raise ForecastValidationError(
            f"Agent '{agent_code}' is inactive."
        )

    return agent


def find_provider(
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
        raise ForecastNotFoundError(
            f"Provider '{provider_code}' was not found."
        )

    return provider


def get_provider_float_snapshot(
    *,
    db: Session,
    agent: Agent,
    provider: Provider,
) -> tuple[Decimal, datetime, str]:
    """Return the selected provider-float snapshot."""

    balance = db.scalar(
        select(ProviderBalance).where(
            ProviderBalance.agent_id == agent.id,
            ProviderBalance.provider_id == provider.id,
        )
    )

    if balance is None:
        raise ForecastDataUnavailableError(
            "The selected Agent has no balance record "
            f"for provider '{provider.code}'."
        )

    return (
        as_decimal(balance.electronic_balance),
        balance.last_update_at,
        balance.freshness_state,
    )


def get_physical_cash_snapshot(
    *,
    db: Session,
    agent: Agent,
) -> tuple[Decimal, datetime, str]:
    """Return the Agent's shared physical-cash snapshot."""

    position = db.scalar(
        select(AgentPosition).where(
            AgentPosition.agent_id == agent.id
        )
    )

    if position is None:
        raise ForecastDataUnavailableError(
            "The selected Agent has no shared-cash position."
        )

    return (
        as_decimal(position.shared_cash),
        position.as_of,
        "fresh",
    )


def get_latest_transaction_time(
    *,
    db: Session,
    agent: Agent,
    provider: Provider | None,
    resource_type: str,
    scenario_id: str | None,
) -> datetime:
    """Find the newest completed transaction in scope."""

    statement = select(
        func.max(Transaction.occurred_at)
    ).where(
        Transaction.agent_id == agent.id,
        Transaction.status == "completed",
    )

    if scenario_id is not None:
        statement = statement.where(
            Transaction.scenario_id == scenario_id
        )

    if resource_type == "provider_float":
        if provider is None:
            raise ForecastValidationError(
                "provider_code is required for "
                "provider-float forecasts."
            )

        statement = statement.where(
            Transaction.provider_id == provider.id
        )

    latest_time = db.scalar(statement)

    if latest_time is None:
        raise ForecastDataUnavailableError(
            "No completed transactions are available "
            "for the selected forecast."
        )

    return latest_time


def get_transactions_in_window(
    *,
    db: Session,
    agent: Agent,
    provider: Provider | None,
    resource_type: str,
    scenario_id: str | None,
    window_start: datetime,
    window_end: datetime,
) -> list[Transaction]:
    """Return completed transactions in the forecast window."""

    statement = (
        select(Transaction)
        .where(
            Transaction.agent_id == agent.id,
            Transaction.status == "completed",
            Transaction.occurred_at >= window_start,
            Transaction.occurred_at <= window_end,
        )
        .order_by(
            Transaction.occurred_at,
            Transaction.id,
        )
    )

    if scenario_id is not None:
        statement = statement.where(
            Transaction.scenario_id == scenario_id
        )

    if resource_type == "provider_float":
        if provider is None:
            raise ForecastValidationError(
                "provider_code is required for "
                "provider-float forecasts."
            )

        statement = statement.where(
            Transaction.provider_id == provider.id
        )

    return list(
        db.scalars(statement).all()
    )


def forecast_liquidity_runway(
    db: Session,
    request: LiquidityRunwayRequest,
) -> LiquidityRunwayResponse:
    """Calculate an explainable liquidity runway forecast."""

    agent = find_agent(
        db,
        request.agent_code,
    )

    provider: Provider | None = None

    if request.resource_type == "provider_float":
        if not request.provider_code:
            raise ForecastValidationError(
                "provider_code is required when resource_type "
                "is 'provider_float'."
            )

        provider = find_provider(
            db,
            request.provider_code,
        )

        (
            current_balance,
            balance_as_of,
            freshness_state,
        ) = get_provider_float_snapshot(
            db=db,
            agent=agent,
            provider=provider,
        )

        safety_threshold = (
            PROVIDER_FLOAT_SAFETY_RESERVE
        )

    else:
        (
            current_balance,
            balance_as_of,
            freshness_state,
        ) = get_physical_cash_snapshot(
            db=db,
            agent=agent,
        )

        safety_threshold = (
            PHYSICAL_CASH_SAFETY_RESERVE
        )

    forecast_as_of = get_latest_transaction_time(
        db=db,
        agent=agent,
        provider=provider,
        resource_type=request.resource_type,
        scenario_id=request.scenario_id,
    )

    window_start = forecast_as_of - timedelta(
        hours=request.lookback_hours
    )

    transactions = get_transactions_in_window(
        db=db,
        agent=agent,
        provider=provider,
        resource_type=request.resource_type,
        scenario_id=request.scenario_id,
        window_start=window_start,
        window_end=forecast_as_of,
    )

    if not transactions:
        raise ForecastDataUnavailableError(
            "No completed transactions were found "
            "inside the selected lookback window."
        )

    (
        gross_consumption,
        gross_replenishment,
    ) = calculate_resource_flows(
        transactions=transactions,
        resource_type=request.resource_type,
    )

    net_consumption = (
        gross_consumption
        - gross_replenishment
    )

    observation_hours = Decimal(
        request.lookback_hours
    )

    net_consumption_per_hour = (
        net_consumption / observation_hours
    ).quantize(
        TWO_DECIMAL_PLACES
    )

    balance_above_threshold = max(
        current_balance - safety_threshold,
        ZERO,
    )

    runway_hours: Decimal | None = None
    estimated_breach_time: datetime | None = None

    if current_balance <= safety_threshold:
        runway_hours = ZERO
        estimated_breach_time = forecast_as_of

    elif net_consumption_per_hour > ZERO:
        runway_hours = (
            balance_above_threshold
            / net_consumption_per_hour
        ).quantize(
            TWO_DECIMAL_PLACES
        )

        estimated_breach_time = (
            forecast_as_of
            + timedelta(
                seconds=float(
                    runway_hours
                    * Decimal("3600")
                )
            )
        )

    risk_level = calculate_risk_level(
        current_balance=current_balance,
        safety_threshold=safety_threshold,
        sample_count=len(transactions),
        net_consumption_per_hour=(
            net_consumption_per_hour
        ),
        runway_hours=runway_hours,
        warning_threshold_hours=(
            request.warning_threshold_hours
        ),
    )

    confidence = confidence_for_forecast(
        freshness_state=freshness_state,
        sample_count=len(transactions),
    )

    provider_text = (
        provider.code
        if provider is not None
        else "all providers"
    )

    explanation_factors = [
        (
            f"Current balance: {current_balance:.2f}; "
            f"prototype safety threshold: "
            f"{safety_threshold:.2f}."
        ),
        (
            f"Completed transactions analyzed: "
            f"{len(transactions)} over "
            f"{request.lookback_hours} hours."
        ),
        (
            f"Gross consumption: "
            f"{gross_consumption:.2f}; gross replenishment: "
            f"{gross_replenishment:.2f}."
        ),
        (
            f"Net consumption per hour: "
            f"{net_consumption_per_hour:.2f}."
        ),
        (
            f"Data freshness state: {freshness_state}; "
            f"confidence: {confidence:.2f}."
        ),
        (
            f"Resource scope: {provider_text}. "
            "The estimate assumes the recent pattern continues."
        ),
    ]

    human_review_required = (
        risk_level
        in {
            "CRITICAL",
            "HIGH",
            "INSUFFICIENT_HISTORY",
        }
        or freshness_state != "fresh"
    )

    return LiquidityRunwayResponse(
        agent_code=agent.code,
        resource_type=request.resource_type,
        provider_code=(
            provider.code
            if provider is not None
            else None
        ),
        scenario_id=request.scenario_id,
        current_balance=current_balance,
        safety_threshold=safety_threshold,
        balance_above_threshold=(
            balance_above_threshold
        ),
        balance_as_of=balance_as_of,
        freshness_state=freshness_state,
        forecast_as_of=forecast_as_of,
        window_start=window_start,
        window_end=forecast_as_of,
        lookback_hours=request.lookback_hours,
        completed_transaction_count=(
            len(transactions)
        ),
        gross_consumption=(
            gross_consumption
        ),
        gross_replenishment=(
            gross_replenishment
        ),
        net_consumption=net_consumption,
        net_consumption_per_hour=(
            net_consumption_per_hour
        ),
        runway_hours=runway_hours,
        estimated_threshold_breach_time=(
            estimated_breach_time
        ),
        risk_level=risk_level,
        confidence=confidence,
        warning_message=build_warning_message(
            risk_level=risk_level,
            runway_hours=runway_hours,
        ),
        explanation_factors=(
            explanation_factors
        ),
        human_review_required=(
            human_review_required
        ),
        automatic_action_taken=False,
    )