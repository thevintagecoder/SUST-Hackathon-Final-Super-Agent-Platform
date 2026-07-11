"""Evaluate anomaly detection against synthetic ground truth."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.schemas.anomaly import (
    AnomalyDetectionRequest,
)
from backend.app.services.anomaly_service import (
    detect_anomalies_for_request,
)


DEFAULT_GROUND_TRUTH_PATH = Path(
    "synthetic_data/generated/demo/ground_truth.json"
)

DEFAULT_SCENARIO_IDS = (
    "NORMAL-001",
    "REPEATED-001",
)

DEFAULT_AGENT_CODE = "AGENT-SYL-001"

FOUR_DECIMAL_PLACES = Decimal("0.0001")


@dataclass(frozen=True)
class ScenarioAnomalyOutcome:
    """Store one scenario's expected and predicted result."""

    scenario_id: str
    expected_anomaly: bool
    predicted_anomaly: bool

    category: str | None
    severity: str
    confidence: Decimal

    classification: str
    passed: bool


@dataclass(frozen=True)
class AnomalyEvaluationSummary:
    """Store anomaly-classification evaluation metrics."""

    outcomes: tuple[ScenarioAnomalyOutcome, ...]

    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    precision: Decimal
    recall: Decimal
    false_positive_rate: Decimal

    passed: bool


def read_ground_truth(
    path: Path,
) -> dict[str, Any]:
    """Read the generated synthetic ground truth."""

    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def find_scenario_ground_truth(
    *,
    ground_truth: dict[str, Any],
    scenario_id: str,
) -> dict[str, Any]:
    """Find one scenario in the ground-truth document."""

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


def parse_expected_anomaly(
    value: Any,
) -> bool:
    """Convert a ground-truth anomaly label to bool."""

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized_value = value.strip().lower()

        if normalized_value == "true":
            return True

        if normalized_value == "false":
            return False

    raise ValueError(
        "anomaly_expected must be either true or false."
    )


def calculate_rate(
    *,
    numerator: int,
    denominator: int,
) -> Decimal:
    """Calculate a safely rounded evaluation rate."""

    if denominator == 0:
        return Decimal("0.0000")

    return (
        Decimal(numerator)
        / Decimal(denominator)
    ).quantize(
        FOUR_DECIMAL_PLACES
    )


def classify_prediction(
    *,
    expected_anomaly: bool,
    predicted_anomaly: bool,
) -> str:
    """Return the confusion-matrix classification."""

    if expected_anomaly and predicted_anomaly:
        return "TRUE_POSITIVE"

    if (
        not expected_anomaly
        and predicted_anomaly
    ):
        return "FALSE_POSITIVE"

    if (
        not expected_anomaly
        and not predicted_anomaly
    ):
        return "TRUE_NEGATIVE"

    return "FALSE_NEGATIVE"


def evaluate_anomaly_scenarios(
    *,
    db: Session,
    ground_truth_path: Path,
    scenario_ids: tuple[str, ...] = (
        DEFAULT_SCENARIO_IDS
    ),
    agent_code: str = DEFAULT_AGENT_CODE,
) -> AnomalyEvaluationSummary:
    """Evaluate anomaly predictions for synthetic scenarios."""

    ground_truth = read_ground_truth(
        ground_truth_path
    )

    outcomes: list[
        ScenarioAnomalyOutcome
    ] = []

    for scenario_id in scenario_ids:
        scenario_ground_truth = (
            find_scenario_ground_truth(
                ground_truth=ground_truth,
                scenario_id=scenario_id,
            )
        )

        expected_anomaly = (
            parse_expected_anomaly(
                scenario_ground_truth[
                    "anomaly_expected"
                ]
            )
        )

        result = detect_anomalies_for_request(
            db=db,
            request=AnomalyDetectionRequest(
                agent_code=agent_code,
                provider_code=None,
                scenario_id=scenario_id,
                recent_window_minutes=60,
                baseline_window_minutes=60,
                amount_tolerance=Decimal(
                    "100.00"
                ),
                minimum_repeated_count=5,
                velocity_multiplier=Decimal(
                    "2.00"
                ),
            ),
        )

        classification = classify_prediction(
            expected_anomaly=(
                expected_anomaly
            ),
            predicted_anomaly=(
                result.anomaly_detected
            ),
        )

        outcomes.append(
            ScenarioAnomalyOutcome(
                scenario_id=scenario_id,
                expected_anomaly=(
                    expected_anomaly
                ),
                predicted_anomaly=(
                    result.anomaly_detected
                ),
                category=result.category,
                severity=result.severity,
                confidence=result.confidence,
                classification=classification,
                passed=(
                    expected_anomaly
                    == result.anomaly_detected
                ),
            )
        )

    true_positives = sum(
        outcome.classification
        == "TRUE_POSITIVE"
        for outcome in outcomes
    )

    false_positives = sum(
        outcome.classification
        == "FALSE_POSITIVE"
        for outcome in outcomes
    )

    true_negatives = sum(
        outcome.classification
        == "TRUE_NEGATIVE"
        for outcome in outcomes
    )

    false_negatives = sum(
        outcome.classification
        == "FALSE_NEGATIVE"
        for outcome in outcomes
    )

    precision = calculate_rate(
        numerator=true_positives,
        denominator=(
            true_positives
            + false_positives
        ),
    )

    recall = calculate_rate(
        numerator=true_positives,
        denominator=(
            true_positives
            + false_negatives
        ),
    )

    false_positive_rate = calculate_rate(
        numerator=false_positives,
        denominator=(
            false_positives
            + true_negatives
        ),
    )

    return AnomalyEvaluationSummary(
        outcomes=tuple(outcomes),
        true_positives=true_positives,
        false_positives=false_positives,
        true_negatives=true_negatives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
        false_positive_rate=(
            false_positive_rate
        ),
        passed=(
            false_positives == 0
            and false_negatives == 0
        ),
    )


def print_evaluation(
    result: AnomalyEvaluationSummary,
) -> None:
    """Print scenario outcomes and metrics."""

    print("Anomaly evaluation completed.")

    for outcome in result.outcomes:
        print()
        print(
            f"Scenario: {outcome.scenario_id}"
        )
        print(
            "Expected anomaly: "
            f"{outcome.expected_anomaly}"
        )
        print(
            "Predicted anomaly: "
            f"{outcome.predicted_anomaly}"
        )
        print(
            "Classification: "
            f"{outcome.classification}"
        )
        print(
            f"Category: {outcome.category}"
        )
        print(
            f"Severity: {outcome.severity}"
        )
        print(
            f"Confidence: {outcome.confidence}"
        )
        print(
            f"Scenario passed: {outcome.passed}"
        )

    print()
    print(
        "True positives: "
        f"{result.true_positives}"
    )
    print(
        "False positives: "
        f"{result.false_positives}"
    )
    print(
        "True negatives: "
        f"{result.true_negatives}"
    )
    print(
        "False negatives: "
        f"{result.false_negatives}"
    )
    print(
        f"Precision: {result.precision}"
    )
    print(
        f"Recall: {result.recall}"
    )
    print(
        "False-positive rate: "
        f"{result.false_positive_rate}"
    )
    print(
        f"Evaluation passed: {result.passed}"
    )


def main() -> None:
    """Run anomaly evaluation from the terminal."""

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate anomaly detection against "
            "synthetic ground truth."
        )
    )

    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=DEFAULT_GROUND_TRUTH_PATH,
    )

    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=list(
            DEFAULT_SCENARIO_IDS
        ),
    )

    parser.add_argument(
        "--agent-code",
        default=DEFAULT_AGENT_CODE,
    )

    arguments = parser.parse_args()

    with SessionLocal() as db:
        result = evaluate_anomaly_scenarios(
            db=db,
            ground_truth_path=(
                arguments.ground_truth
            ),
            scenario_ids=tuple(
                arguments.scenarios
            ),
            agent_code=(
                arguments.agent_code
            ),
        )

    print_evaluation(result)


if __name__ == "__main__":
    main()