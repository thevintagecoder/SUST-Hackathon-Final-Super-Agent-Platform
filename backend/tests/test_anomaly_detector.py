"""Tests for deterministic anomaly-detection rules."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from backend.app.analytics.anomaly_detector import (
    TransactionObservation,
    detect_repeated_amounts_and_velocity,
)


ANALYSIS_TIME = datetime(
    2026,
    7,
    11,
    12,
    0,
    tzinfo=UTC,
)


def observation(
    *,
    transaction_id: str,
    amount: str,
    minutes_before: int,
) -> TransactionObservation:
    """Create one deterministic transaction observation."""

    return TransactionObservation(
        transaction_id=transaction_id,
        amount=Decimal(amount),
        occurred_at=(
            ANALYSIS_TIME
            - timedelta(
                minutes=minutes_before
            )
        ),
    )


def test_repeated_amounts_and_velocity_require_review() -> None:
    """Both signals should produce a high-severity result."""

    transactions = [
        observation(
            transaction_id="TXN-BASE-001",
            amount="3000.00",
            minutes_before=110,
        ),
        observation(
            transaction_id="TXN-BASE-002",
            amount="7500.00",
            minutes_before=80,
        ),
        observation(
            transaction_id="TXN-RECENT-001",
            amount="10000.00",
            minutes_before=50,
        ),
        observation(
            transaction_id="TXN-RECENT-002",
            amount="10020.00",
            minutes_before=40,
        ),
        observation(
            transaction_id="TXN-RECENT-003",
            amount="9990.00",
            minutes_before=30,
        ),
        observation(
            transaction_id="TXN-RECENT-004",
            amount="10010.00",
            minutes_before=20,
        ),
        observation(
            transaction_id="TXN-RECENT-005",
            amount="10030.00",
            minutes_before=10,
        ),
        observation(
            transaction_id="TXN-RECENT-006",
            amount="10040.00",
            minutes_before=0,
        ),
    ]

    result = (
        detect_repeated_amounts_and_velocity(
            transactions=transactions
        )
    )

    assert result.anomaly_detected is True

    assert (
        result.category
        == "repeated_amounts_and_velocity"
    )

    assert result.severity == "HIGH"
    assert result.decision == "REQUIRES_REVIEW"

    assert result.recent_transaction_count == 6
    assert result.baseline_transaction_count == 2

    assert (
        result.velocity_ratio
        == Decimal("3.00")
    )

    assert result.repeated_amount_signal is True
    assert result.velocity_signal is True

    assert result.repeated_transaction_count == 6

    assert (
        result.repeated_amount_min
        == Decimal("9990.00")
    )

    assert (
        result.repeated_amount_max
        == Decimal("10040.00")
    )

    assert result.confidence == Decimal("0.90")
    assert result.human_review_required is True
    assert result.automatic_action_taken is False

    assert "requires human review" in (
        result.warning_message.lower()
    )

    assert "fraud" not in (
        result.warning_message.lower()
    )


def test_repeated_amounts_work_without_velocity_spike() -> None:
    """Repeated amounts alone should still require review."""

    transactions = [
        observation(
            transaction_id="TXN-BASE-001",
            amount="2000.00",
            minutes_before=110,
        ),
        observation(
            transaction_id="TXN-BASE-002",
            amount="4500.00",
            minutes_before=100,
        ),
        observation(
            transaction_id="TXN-BASE-003",
            amount="7000.00",
            minutes_before=90,
        ),
        observation(
            transaction_id="TXN-BASE-004",
            amount="8500.00",
            minutes_before=80,
        ),
        observation(
            transaction_id="TXN-BASE-005",
            amount="12000.00",
            minutes_before=70,
        ),
        observation(
            transaction_id="TXN-RECENT-001",
            amount="5000.00",
            minutes_before=50,
        ),
        observation(
            transaction_id="TXN-RECENT-002",
            amount="5010.00",
            minutes_before=40,
        ),
        observation(
            transaction_id="TXN-RECENT-003",
            amount="4990.00",
            minutes_before=30,
        ),
        observation(
            transaction_id="TXN-RECENT-004",
            amount="5020.00",
            minutes_before=20,
        ),
        observation(
            transaction_id="TXN-RECENT-005",
            amount="5005.00",
            minutes_before=0,
        ),
    ]

    result = (
        detect_repeated_amounts_and_velocity(
            transactions=transactions
        )
    )

    assert result.anomaly_detected is True
    assert result.category == "repeated_amounts"
    assert result.severity == "MEDIUM"

    assert result.repeated_amount_signal is True
    assert result.velocity_signal is False

    assert (
        result.velocity_ratio
        == Decimal("1.00")
    )


def test_normal_varied_activity_does_not_trigger() -> None:
    """Varied amounts and stable velocity should remain normal."""

    transactions = [
        observation(
            transaction_id="TXN-BASE-001",
            amount="1000.00",
            minutes_before=110,
        ),
        observation(
            transaction_id="TXN-BASE-002",
            amount="2500.00",
            minutes_before=100,
        ),
        observation(
            transaction_id="TXN-BASE-003",
            amount="4200.00",
            minutes_before=90,
        ),
        observation(
            transaction_id="TXN-BASE-004",
            amount="7000.00",
            minutes_before=70,
        ),
        observation(
            transaction_id="TXN-RECENT-001",
            amount="1500.00",
            minutes_before=50,
        ),
        observation(
            transaction_id="TXN-RECENT-002",
            amount="3200.00",
            minutes_before=40,
        ),
        observation(
            transaction_id="TXN-RECENT-003",
            amount="5600.00",
            minutes_before=20,
        ),
        observation(
            transaction_id="TXN-RECENT-004",
            amount="9100.00",
            minutes_before=0,
        ),
    ]

    result = (
        detect_repeated_amounts_and_velocity(
            transactions=transactions
        )
    )

    assert result.anomaly_detected is False
    assert result.category is None
    assert result.severity == "NONE"
    assert result.decision == "NO_ALERT"

    assert result.repeated_amount_signal is False
    assert result.velocity_signal is False

    assert (
        result.velocity_ratio
        == Decimal("1.00")
    )

    assert result.human_review_required is False
    assert result.automatic_action_taken is False


def test_empty_history_returns_safe_result() -> None:
    """Empty history should not create an unsupported alert."""

    result = (
        detect_repeated_amounts_and_velocity(
            transactions=[]
        )
    )

    assert result.anomaly_detected is False
    assert result.category is None
    assert result.analysis_as_of is None
    assert result.confidence == Decimal("0.20")


def test_invalid_threshold_is_rejected() -> None:
    """Invalid detector thresholds should fail clearly."""

    with pytest.raises(
        ValueError,
        match="minimum_repeated_count",
    ):
        detect_repeated_amounts_and_velocity(
            transactions=[],
            minimum_repeated_count=1,
        )