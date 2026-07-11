"""Evaluate runway forecasts against synthetic ground truth."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.schemas.forecast import (
    LiquidityRunwayRequest,
)
from backend.app.services.forecast_service import (
    forecast_liquidity_runway,
)


DEFAULT_GROUND_TRUTH_PATH = Path(
    "synthetic_data/generated/demo/ground_truth.json"
)
DEFAULT_SCENARIO_ID = "FORECAST-001"

TWO_DECIMAL_PLACES = Decimal("0.01")


@dataclass(frozen=True)
class ForecastEvaluationResult:
    """Store deterministic forecast evaluation metrics."""

    scenario_id: str

    predicted_risk_level: str
    expected_risk_level: str

    predicted_runway_hours: Decimal | None
    expected_runway_hours: Decimal

    predicted_breach_time: datetime | None
    actual_breach_time: datetime

    forecast_error_hours: Decimal | None
    shortage_warning_lead_time_hours: Decimal | None

    warning_triggered: bool
    passed: bool


def parse_datetime(
    value: str,
) -> datetime:
    """Parse an ISO-8601 UTC datetime."""

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


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


def hours_between(
    first: datetime,
    second: datetime,
) -> Decimal:
    """Return an absolute duration in hours."""

    first_utc = normalize_to_utc(
        first
    )
    second_utc = normalize_to_utc(
        second
    )

    seconds = abs(
        Decimal(
            str(
                (
                    first_utc
                    - second_utc
                ).total_seconds()
            )
        )
    )

    return (
        seconds / Decimal("3600")
    ).quantize(
        TWO_DECIMAL_PLACES
    )


def positive_hours_between(
    later: datetime,
    earlier: datetime,
) -> Decimal:
    """Return a nonnegative duration in hours."""

    later_utc = normalize_to_utc(
        later
    )
    earlier_utc = normalize_to_utc(
        earlier
    )

    seconds = max(
        (
            later_utc
            - earlier_utc
        ).total_seconds(),
        0,
    )

    return (
        Decimal(str(seconds))
        / Decimal("3600")
    ).quantize(
        TWO_DECIMAL_PLACES
    )


def read_ground_truth(
    path: Path,
) -> dict[str, Any]:
    """Read the generated ground-truth document."""

    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def find_scenario_ground_truth(
    ground_truth: dict[str, Any],
    scenario_id: str,
) -> dict[str, Any]:
    """Return one scenario's ground-truth record."""

    for scenario in ground_truth[
        "scenarios"
    ]:
        if (
            scenario["scenario_id"]
            == scenario_id
        ):
            return scenario

    raise ValueError(
        "Ground truth does not contain scenario "
        f"'{scenario_id}'."
    )


def evaluate_forecast_scenario(
    *,
    db: Session,
    ground_truth_path: Path,
    scenario_id: str = DEFAULT_SCENARIO_ID,
) -> ForecastEvaluationResult:
    """Run and evaluate one deterministic forecast."""

    ground_truth = read_ground_truth(
        ground_truth_path
    )

    scenario = find_scenario_ground_truth(
        ground_truth,
        scenario_id,
    )

    configuration = scenario.get(
        "forecast_evaluation"
    )

    if configuration is None:
        raise ValueError(
            "The selected scenario does not contain "
            "forecast-evaluation ground truth."
        )

    forecast = forecast_liquidity_runway(
        db=db,
        request=LiquidityRunwayRequest(
            agent_code=configuration[
                "agent_code"
            ],
            resource_type=configuration[
                "resource_type"
            ],
            provider_code=configuration[
                "provider_code"
            ],
            scenario_id=scenario_id,
            lookback_hours=configuration[
                "lookback_hours"
            ],
            warning_threshold_hours=Decimal(
                configuration[
                    "warning_threshold_hours"
                ]
            ),
        ),
    )

    actual_breach_time = parse_datetime(
        configuration[
            "actual_threshold_breach_time"
        ]
    )

    expected_runway_hours = Decimal(
        configuration[
            "expected_runway_hours"
        ]
    )

    expected_error_hours = Decimal(
        configuration[
            "expected_forecast_error_hours"
        ]
    )

    expected_lead_time_hours = Decimal(
        configuration[
            "expected_warning_lead_time_hours"
        ]
    )

    forecast_error_hours: Decimal | None = None

    if (
        forecast.estimated_threshold_breach_time
        is not None
    ):
        forecast_error_hours = hours_between(
            forecast.estimated_threshold_breach_time,
            actual_breach_time,
        )

    warning_triggered = (
        forecast.risk_level
        in {
            "HIGH",
            "CRITICAL",
        }
    )

    warning_lead_time: Decimal | None = None

    if warning_triggered:
        warning_lead_time = (
            positive_hours_between(
                actual_breach_time,
                forecast.forecast_as_of,
            )
        )

    passed = (
        forecast.risk_level
        == configuration[
            "expected_risk_level"
        ]
        and forecast.runway_hours
        == expected_runway_hours
        and forecast_error_hours
        == expected_error_hours
        and warning_lead_time
        == expected_lead_time_hours
    )

    return ForecastEvaluationResult(
        scenario_id=scenario_id,
        predicted_risk_level=(
            forecast.risk_level
        ),
        expected_risk_level=configuration[
            "expected_risk_level"
        ],
        predicted_runway_hours=(
            forecast.runway_hours
        ),
        expected_runway_hours=(
            expected_runway_hours
        ),
        predicted_breach_time=(
            forecast
            .estimated_threshold_breach_time
        ),
        actual_breach_time=(
            actual_breach_time
        ),
        forecast_error_hours=(
            forecast_error_hours
        ),
        shortage_warning_lead_time_hours=(
            warning_lead_time
        ),
        warning_triggered=(
            warning_triggered
        ),
        passed=passed,
    )


def print_evaluation(
    result: ForecastEvaluationResult,
) -> None:
    """Print evaluation metrics for human review."""

    print("Forecast evaluation completed.")
    print(f"Scenario: {result.scenario_id}")
    print(
        "Predicted risk level: "
        f"{result.predicted_risk_level}"
    )
    print(
        "Expected risk level: "
        f"{result.expected_risk_level}"
    )
    print(
        "Predicted runway hours: "
        f"{result.predicted_runway_hours}"
    )
    print(
        "Expected runway hours: "
        f"{result.expected_runway_hours}"
    )
    print(
        "Predicted breach time: "
        f"{result.predicted_breach_time}"
    )
    print(
        "Actual breach time: "
        f"{result.actual_breach_time}"
    )
    print(
        "Forecast error hours: "
        f"{result.forecast_error_hours}"
    )
    print(
        "Shortage-warning lead time hours: "
        f"{result.shortage_warning_lead_time_hours}"
    )
    print(
        "Warning triggered: "
        f"{result.warning_triggered}"
    )
    print(
        "Evaluation passed: "
        f"{result.passed}"
    )


def main() -> None:
    """Run forecast evaluation from the command line."""

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a liquidity runway forecast "
            "against synthetic ground truth."
        )
    )

    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=DEFAULT_GROUND_TRUTH_PATH,
    )

    parser.add_argument(
        "--scenario",
        default=DEFAULT_SCENARIO_ID,
    )

    arguments = parser.parse_args()

    with SessionLocal() as db:
        result = evaluate_forecast_scenario(
            db=db,
            ground_truth_path=(
                arguments.ground_truth
            ),
            scenario_id=arguments.scenario,
        )

    print_evaluation(result)


if __name__ == "__main__":
    main()