"""Database integration for explainable anomaly detection."""

from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.analytics.anomaly_detector import (
    TransactionObservation,
    detect_repeated_amounts_and_velocity,
)
from backend.app.models import (
    Agent,
    Provider,
    Transaction,
)
from backend.app.schemas.anomaly import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
)


class AnomalyNotFoundError(Exception):
    """Raised when an Agent or provider cannot be found."""


class AnomalyValidationError(Exception):
    """Raised when an anomaly request is inconsistent."""


def find_agent(
    *,
    db: Session,
    agent_code: str,
) -> Agent:
    """Return an active Agent by code."""

    agent = db.scalar(
        select(Agent).where(
            Agent.code == agent_code
        )
    )

    if agent is None:
        raise AnomalyNotFoundError(
            f"Agent '{agent_code}' was not found."
        )

    if not agent.is_active:
        raise AnomalyValidationError(
            f"Agent '{agent_code}' is inactive."
        )

    return agent


def find_provider(
    *,
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
        raise AnomalyNotFoundError(
            f"Provider '{provider_code}' was not found."
        )

    return provider


def build_transaction_scope(
    *,
    agent: Agent,
    provider: Provider | None,
    scenario_id: str | None,
):
    """Create common database filters for the analysis."""

    filters = [
        Transaction.agent_id == agent.id,
        Transaction.status == "completed",
    ]

    if provider is not None:
        filters.append(
            Transaction.provider_id == provider.id
        )

    if scenario_id is not None:
        filters.append(
            Transaction.scenario_id == scenario_id
        )

    return filters


def detect_anomalies_for_request(
    *,
    db: Session,
    request: AnomalyDetectionRequest,
) -> AnomalyDetectionResponse:
    """Analyze scoped completed transactions."""

    agent = find_agent(
        db=db,
        agent_code=request.agent_code,
    )

    provider: Provider | None = None

    if request.provider_code is not None:
        provider = find_provider(
            db=db,
            provider_code=request.provider_code,
        )

    filters = build_transaction_scope(
        agent=agent,
        provider=provider,
        scenario_id=request.scenario_id,
    )

    analysis_as_of = db.scalar(
        select(
            func.max(
                Transaction.occurred_at
            )
        ).where(
            *filters
        )
    )

    observations: list[
        TransactionObservation
    ] = []

    if analysis_as_of is not None:
        total_window_minutes = (
            request.recent_window_minutes
            + request.baseline_window_minutes
        )

        analysis_window_start = (
            analysis_as_of
            - timedelta(
                minutes=total_window_minutes
            )
        )

        statement = (
            select(Transaction)
            .where(
                *filters,
                Transaction.occurred_at
                > analysis_window_start,
                Transaction.occurred_at
                <= analysis_as_of,
            )
            .order_by(
                Transaction.occurred_at,
                Transaction.id,
            )
        )

        transactions = list(
            db.scalars(
                statement
            ).all()
        )

        observations = [
            TransactionObservation(
                transaction_id=str(
                    transaction.external_id
                ),
                amount=Decimal(
                    str(
                        transaction.amount
                    )
                ),
                occurred_at=(
                    transaction.occurred_at
                ),
            )
            for transaction in transactions
        ]

    result = (
        detect_repeated_amounts_and_velocity(
            transactions=observations,
            recent_window_minutes=(
                request.recent_window_minutes
            ),
            baseline_window_minutes=(
                request.baseline_window_minutes
            ),
            amount_tolerance=(
                request.amount_tolerance
            ),
            minimum_repeated_count=(
                request.minimum_repeated_count
            ),
            velocity_multiplier=(
                request.velocity_multiplier
            ),
        )
    )

    return AnomalyDetectionResponse(
        agent_code=agent.code,
        provider_code=(
            provider.code
            if provider is not None
            else None
        ),
        scenario_id=request.scenario_id,
        anomaly_detected=(
            result.anomaly_detected
        ),
        category=result.category,
        severity=result.severity,
        decision=result.decision,
        analysis_as_of=(
            result.analysis_as_of
        ),
        recent_window_start=(
            result.recent_window_start
        ),
        baseline_window_start=(
            result.baseline_window_start
        ),
        recent_window_minutes=(
            request.recent_window_minutes
        ),
        baseline_window_minutes=(
            request.baseline_window_minutes
        ),
        recent_transaction_count=(
            result.recent_transaction_count
        ),
        baseline_transaction_count=(
            result.baseline_transaction_count
        ),
        velocity_ratio=(
            result.velocity_ratio
        ),
        repeated_amount_signal=(
            result.repeated_amount_signal
        ),
        velocity_signal=(
            result.velocity_signal
        ),
        repeated_transaction_count=(
            result.repeated_transaction_count
        ),
        repeated_amount_min=(
            result.repeated_amount_min
        ),
        repeated_amount_max=(
            result.repeated_amount_max
        ),
        repeated_transaction_ids=list(
            result.repeated_transaction_ids
        ),
        confidence=result.confidence,
        warning_message=(
            result.warning_message
        ),
        explanation_factors=list(
            result.explanation_factors
        ),
        uncertainty=result.uncertainty,
        recommended_next_step=(
            result.recommended_next_step
        ),
        human_review_required=(
            result.human_review_required
        ),
        automatic_action_taken=(
            result.automatic_action_taken
        ),
    )