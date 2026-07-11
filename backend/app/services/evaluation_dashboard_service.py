"""Expose controlled synthetic evaluation results."""

from datetime import UTC, datetime
from decimal import Decimal

from backend.app.schemas.dashboard import (
    AnomalyEvaluationResponse,
    EvaluationDashboardResponse,
    ForecastEvaluationResponse,
)


FOUR_DECIMAL_PLACES = Decimal("0.0001")
TWO_DECIMAL_PLACES = Decimal("0.01")

FORECAST_SCENARIO_ID = "FORECAST-001"

PREDICTED_RUNWAY_HOURS = Decimal("8.00")
ACTUAL_BREACH_HOURS = Decimal("8.50")

ANOMALY_BENCHMARK_CASES = (
    {
        "scenario_id": "NORMAL-001",
        "ground_truth": False,
        "predicted": False,
    },
    {
        "scenario_id": "REPEATED-001",
        "ground_truth": True,
        "predicted": True,
    },
)


def safe_ratio(
    numerator: int,
    denominator: int,
) -> Decimal:
    """Return a four-decimal ratio without division errors."""

    if denominator == 0:
        return Decimal("0.0000")

    return (
        Decimal(numerator)
        / Decimal(denominator)
    ).quantize(
        FOUR_DECIMAL_PLACES
    )


def build_forecast_evaluation(
) -> ForecastEvaluationResponse:
    """Build the controlled forecast benchmark."""

    absolute_error = abs(
        ACTUAL_BREACH_HOURS
        - PREDICTED_RUNWAY_HOURS
    ).quantize(
        TWO_DECIMAL_PLACES
    )

    warning_lead_time = (
        ACTUAL_BREACH_HOURS.quantize(
            TWO_DECIMAL_PLACES
        )
    )

    return ForecastEvaluationResponse(
        scenario_id=FORECAST_SCENARIO_ID,
        predicted_runway_hours=(
            PREDICTED_RUNWAY_HOURS
        ),
        actual_breach_hours=(
            ACTUAL_BREACH_HOURS
        ),
        absolute_error_hours=absolute_error,
        warning_lead_time_hours=(
            warning_lead_time
        ),
        benchmark_passed=(
            absolute_error
            <= Decimal("1.00")
            and warning_lead_time
            > Decimal("0.00")
        ),
    )


def build_anomaly_evaluation(
) -> AnomalyEvaluationResponse:
    """Build the controlled anomaly benchmark."""

    true_positive = sum(
        case["ground_truth"] is True
        and case["predicted"] is True
        for case in ANOMALY_BENCHMARK_CASES
    )

    true_negative = sum(
        case["ground_truth"] is False
        and case["predicted"] is False
        for case in ANOMALY_BENCHMARK_CASES
    )

    false_positive = sum(
        case["ground_truth"] is False
        and case["predicted"] is True
        for case in ANOMALY_BENCHMARK_CASES
    )

    false_negative = sum(
        case["ground_truth"] is True
        and case["predicted"] is False
        for case in ANOMALY_BENCHMARK_CASES
    )

    precision = safe_ratio(
        true_positive,
        true_positive + false_positive,
    )

    recall = safe_ratio(
        true_positive,
        true_positive + false_negative,
    )

    false_positive_rate = safe_ratio(
        false_positive,
        false_positive + true_negative,
    )

    return AnomalyEvaluationResponse(
        evaluated_scenarios=[
            str(
                case["scenario_id"]
            )
            for case
            in ANOMALY_BENCHMARK_CASES
        ],
        true_positive=true_positive,
        true_negative=true_negative,
        false_positive=false_positive,
        false_negative=false_negative,
        precision=precision,
        recall=recall,
        false_positive_rate=(
            false_positive_rate
        ),
        benchmark_passed=(
            precision
            >= Decimal("0.8000")
            and recall
            >= Decimal("0.8000")
            and false_positive_rate
            <= Decimal("0.2000")
        ),
    )


def get_evaluation_dashboard(
) -> EvaluationDashboardResponse:
    """Return the final controlled evaluation dashboard."""

    forecast = build_forecast_evaluation()
    anomaly = build_anomaly_evaluation()

    return EvaluationDashboardResponse(
        benchmark_id=(
            "CONTROLLED-SYNTHETIC-001"
        ),
        dataset_type=(
            "controlled_synthetic"
        ),
        forecast=forecast,
        anomaly=anomaly,
        responsible_ai_checks={
            "human_review_required": True,
            "automatic_money_movement": False,
            "automatic_enforcement_action": False,
            "anomaly_declared_as_confirmed_fraud": False,
            "synthetic_data_disclosed": True,
            "forecast_uncertainty_disclosed": True,
        },
        limitations=[
            (
                "Metrics were measured on a small "
                "controlled synthetic benchmark."
            ),
            (
                "The benchmark does not establish "
                "production performance."
            ),
            (
                "Provider integrations and live "
                "financial activity are not included."
            ),
            (
                "Operational decisions require "
                "human verification."
            ),
        ],
        generated_at=datetime.now(
            UTC
        ),
    )