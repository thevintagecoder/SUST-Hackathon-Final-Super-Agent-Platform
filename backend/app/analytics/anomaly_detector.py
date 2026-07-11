"""Deterministic and explainable transaction anomaly detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal


ZERO = Decimal("0.00")
TWO_DECIMAL_PLACES = Decimal("0.01")

DEFAULT_RECENT_WINDOW_MINUTES = 60
DEFAULT_BASELINE_WINDOW_MINUTES = 60
DEFAULT_AMOUNT_TOLERANCE = Decimal("100.00")
DEFAULT_MINIMUM_REPEATED_COUNT = 5
DEFAULT_VELOCITY_MULTIPLIER = Decimal("2.00")


AnomalyCategory = Literal[
    "repeated_amounts",
    "velocity_spike",
    "repeated_amounts_and_velocity",
]

AnomalySeverity = Literal[
    "NONE",
    "MEDIUM",
    "HIGH",
]

AnomalyDecision = Literal[
    "NO_ALERT",
    "REQUIRES_REVIEW",
]


@dataclass(frozen=True)
class TransactionObservation:
    """Represent the transaction fields used by the detector."""

    transaction_id: str
    amount: Decimal
    occurred_at: datetime


@dataclass(frozen=True)
class AnomalyDetectionResult:
    """Return explainable anomaly-detection evidence."""

    anomaly_detected: bool
    category: AnomalyCategory | None
    severity: AnomalySeverity
    decision: AnomalyDecision

    analysis_as_of: datetime | None
    recent_window_start: datetime | None
    baseline_window_start: datetime | None

    recent_transaction_count: int
    baseline_transaction_count: int
    velocity_ratio: Decimal | None

    repeated_amount_signal: bool
    velocity_signal: bool

    repeated_transaction_count: int
    repeated_amount_min: Decimal | None
    repeated_amount_max: Decimal | None
    repeated_transaction_ids: tuple[str, ...]

    confidence: Decimal
    warning_message: str
    explanation_factors: tuple[str, ...]
    uncertainty: str
    recommended_next_step: str

    human_review_required: bool
    automatic_action_taken: bool = False


def normalize_to_utc(
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


def validate_thresholds(
    *,
    recent_window_minutes: int,
    baseline_window_minutes: int,
    amount_tolerance: Decimal,
    minimum_repeated_count: int,
    velocity_multiplier: Decimal,
) -> None:
    """Validate transparent prototype thresholds."""

    if recent_window_minutes <= 0:
        raise ValueError(
            "recent_window_minutes must be positive."
        )

    if baseline_window_minutes <= 0:
        raise ValueError(
            "baseline_window_minutes must be positive."
        )

    if amount_tolerance < ZERO:
        raise ValueError(
            "amount_tolerance cannot be negative."
        )

    if minimum_repeated_count < 2:
        raise ValueError(
            "minimum_repeated_count must be at least 2."
        )

    if velocity_multiplier <= Decimal("1.00"):
        raise ValueError(
            "velocity_multiplier must be greater than 1."
        )


def find_largest_near_identical_cluster(
    *,
    transactions: list[TransactionObservation],
    amount_tolerance: Decimal,
) -> tuple[TransactionObservation, ...]:
    """Find the largest group whose amount range is within tolerance."""

    if not transactions:
        return ()

    ordered_transactions = sorted(
        transactions,
        key=lambda transaction: (
            transaction.amount,
            normalize_to_utc(
                transaction.occurred_at
            ),
            transaction.transaction_id,
        ),
    )

    best_cluster: tuple[
        TransactionObservation,
        ...
    ] = ()

    left_index = 0

    for right_index, transaction in enumerate(
        ordered_transactions
    ):
        while (
            transaction.amount
            - ordered_transactions[
                left_index
            ].amount
            > amount_tolerance
        ):
            left_index += 1

        candidate_cluster = tuple(
            ordered_transactions[
                left_index : right_index + 1
            ]
        )

        if len(candidate_cluster) > len(
            best_cluster
        ):
            best_cluster = candidate_cluster

    return best_cluster


def classify_category(
    *,
    repeated_amount_signal: bool,
    velocity_signal: bool,
) -> AnomalyCategory | None:
    """Classify the signals using understandable categories."""

    if repeated_amount_signal and velocity_signal:
        return "repeated_amounts_and_velocity"

    if repeated_amount_signal:
        return "repeated_amounts"

    if velocity_signal:
        return "velocity_spike"

    return None


def confidence_for_signals(
    *,
    repeated_amount_signal: bool,
    velocity_signal: bool,
    baseline_available: bool,
) -> Decimal:
    """Return a transparent prototype confidence value."""

    if repeated_amount_signal and velocity_signal:
        return Decimal("0.90")

    if repeated_amount_signal:
        if baseline_available:
            return Decimal("0.78")

        return Decimal("0.65")

    if velocity_signal:
        return Decimal("0.68")

    return Decimal("0.35")


def warning_for_category(
    category: AnomalyCategory | None,
) -> str:
    """Create responsible anomaly-warning language."""

    if category == "repeated_amounts_and_velocity":
        return (
            "Repeated or near-identical transaction amounts "
            "occurred alongside increased transaction velocity. "
            "This unusual activity requires human review."
        )

    if category == "repeated_amounts":
        return (
            "Repeated or near-identical transaction amounts were "
            "found in the recent window. The pattern requires "
            "human review."
        )

    if category == "velocity_spike":
        return (
            "Transaction velocity increased compared with the "
            "preceding baseline window. The pattern requires "
            "human review."
        )

    return (
        "The selected transaction window did not meet the "
        "prototype anomaly thresholds."
    )


def empty_detection_result() -> AnomalyDetectionResult:
    """Return a safe result when no transactions are available."""

    return AnomalyDetectionResult(
        anomaly_detected=False,
        category=None,
        severity="NONE",
        decision="NO_ALERT",
        analysis_as_of=None,
        recent_window_start=None,
        baseline_window_start=None,
        recent_transaction_count=0,
        baseline_transaction_count=0,
        velocity_ratio=None,
        repeated_amount_signal=False,
        velocity_signal=False,
        repeated_transaction_count=0,
        repeated_amount_min=None,
        repeated_amount_max=None,
        repeated_transaction_ids=(),
        confidence=Decimal("0.20"),
        warning_message=(
            "No completed transactions were available for "
            "anomaly analysis."
        ),
        explanation_factors=(
            "No transaction observations were supplied.",
        ),
        uncertainty=(
            "Anomaly status cannot be evaluated without "
            "transaction history."
        ),
        recommended_next_step=(
            "Verify that the synthetic transaction data was "
            "loaded before requesting anomaly analysis."
        ),
        human_review_required=False,
        automatic_action_taken=False,
    )


def detect_repeated_amounts_and_velocity(
    *,
    transactions: list[TransactionObservation],
    recent_window_minutes: int = (
        DEFAULT_RECENT_WINDOW_MINUTES
    ),
    baseline_window_minutes: int = (
        DEFAULT_BASELINE_WINDOW_MINUTES
    ),
    amount_tolerance: Decimal = (
        DEFAULT_AMOUNT_TOLERANCE
    ),
    minimum_repeated_count: int = (
        DEFAULT_MINIMUM_REPEATED_COUNT
    ),
    velocity_multiplier: Decimal = (
        DEFAULT_VELOCITY_MULTIPLIER
    ),
) -> AnomalyDetectionResult:
    """Detect repeated amounts and transaction-velocity changes."""

    validate_thresholds(
        recent_window_minutes=(
            recent_window_minutes
        ),
        baseline_window_minutes=(
            baseline_window_minutes
        ),
        amount_tolerance=amount_tolerance,
        minimum_repeated_count=(
            minimum_repeated_count
        ),
        velocity_multiplier=velocity_multiplier,
    )

    if not transactions:
        return empty_detection_result()

    analysis_as_of = max(
        normalize_to_utc(
            transaction.occurred_at
        )
        for transaction in transactions
    )

    recent_window_start = (
        analysis_as_of
        - timedelta(
            minutes=recent_window_minutes
        )
    )

    baseline_window_start = (
        recent_window_start
        - timedelta(
            minutes=baseline_window_minutes
        )
    )

    recent_transactions = [
        transaction
        for transaction in transactions
        if (
            recent_window_start
            < normalize_to_utc(
                transaction.occurred_at
            )
            <= analysis_as_of
        )
    ]

    baseline_transactions = [
        transaction
        for transaction in transactions
        if (
            baseline_window_start
            < normalize_to_utc(
                transaction.occurred_at
            )
            <= recent_window_start
        )
    ]

    repeated_cluster = (
        find_largest_near_identical_cluster(
            transactions=recent_transactions,
            amount_tolerance=amount_tolerance,
        )
    )

    repeated_amount_signal = (
        len(repeated_cluster)
        >= minimum_repeated_count
    )

    baseline_count = len(
        baseline_transactions
    )

    recent_count = len(
        recent_transactions
    )

    velocity_ratio: Decimal | None = None
    velocity_signal = False

    if baseline_count > 0:
        velocity_ratio = (
            Decimal(recent_count)
            / Decimal(baseline_count)
        ).quantize(
            TWO_DECIMAL_PLACES
        )

        velocity_signal = (
            velocity_ratio
            >= velocity_multiplier
        )

    category = classify_category(
        repeated_amount_signal=(
            repeated_amount_signal
        ),
        velocity_signal=velocity_signal,
    )

    anomaly_detected = category is not None

    severity: AnomalySeverity

    if (
        repeated_amount_signal
        and velocity_signal
    ):
        severity = "HIGH"
    elif anomaly_detected:
        severity = "MEDIUM"
    else:
        severity = "NONE"

    confidence = confidence_for_signals(
        repeated_amount_signal=(
            repeated_amount_signal
        ),
        velocity_signal=velocity_signal,
        baseline_available=(
            baseline_count > 0
        ),
    )

    repeated_amount_min: Decimal | None = None
    repeated_amount_max: Decimal | None = None

    if repeated_cluster:
        repeated_amount_min = min(
            transaction.amount
            for transaction in repeated_cluster
        )

        repeated_amount_max = max(
            transaction.amount
            for transaction in repeated_cluster
        )

    velocity_explanation: str

    if velocity_ratio is None:
        velocity_explanation = (
            "Velocity comparison was not available because "
            "the baseline window contained no transactions."
        )
    else:
        velocity_explanation = (
            f"Velocity ratio: {velocity_ratio:.2f}; "
            f"prototype trigger: "
            f"{velocity_multiplier:.2f}."
        )

    explanation_factors = (
        (
            f"Recent transactions: {recent_count} in "
            f"{recent_window_minutes} minutes."
        ),
        (
            f"Baseline transactions: {baseline_count} in "
            f"{baseline_window_minutes} minutes."
        ),
        velocity_explanation,
        (
            f"Largest near-identical amount group: "
            f"{len(repeated_cluster)} transactions."
        ),
        (
            f"Amount tolerance: "
            f"{amount_tolerance:.2f}; minimum repeat "
            f"count: {minimum_repeated_count}."
        ),
    )

    if baseline_count == 0:
        uncertainty = (
            "Velocity confidence is limited because the "
            "preceding baseline window had no observations. "
            "The repeated-amount evidence remains visible."
        )
    else:
        uncertainty = (
            "This deterministic rule identifies unusual "
            "patterns only. A local event, customer demand, "
            "or batch activity may provide a legitimate "
            "explanation."
        )

    if anomaly_detected:
        recommended_next_step = (
            "Ask the assigned operations owner to review the "
            "listed synthetic transactions, verify data "
            "freshness, and record a possible legitimate "
            "explanation."
        )
    else:
        recommended_next_step = (
            "Continue monitoring and retain the current "
            "transaction evidence for comparison."
        )

    return AnomalyDetectionResult(
        anomaly_detected=anomaly_detected,
        category=category,
        severity=severity,
        decision=(
            "REQUIRES_REVIEW"
            if anomaly_detected
            else "NO_ALERT"
        ),
        analysis_as_of=analysis_as_of,
        recent_window_start=(
            recent_window_start
        ),
        baseline_window_start=(
            baseline_window_start
        ),
        recent_transaction_count=(
            recent_count
        ),
        baseline_transaction_count=(
            baseline_count
        ),
        velocity_ratio=velocity_ratio,
        repeated_amount_signal=(
            repeated_amount_signal
        ),
        velocity_signal=velocity_signal,
        repeated_transaction_count=(
            len(repeated_cluster)
        ),
        repeated_amount_min=(
            repeated_amount_min
        ),
        repeated_amount_max=(
            repeated_amount_max
        ),
        repeated_transaction_ids=tuple(
            transaction.transaction_id
            for transaction in repeated_cluster
        ),
        confidence=confidence,
        warning_message=warning_for_category(
            category
        ),
        explanation_factors=(
            explanation_factors
        ),
        uncertainty=uncertainty,
        recommended_next_step=(
            recommended_next_step
        ),
        human_review_required=(
            anomaly_detected
        ),
        automatic_action_taken=False,
    )