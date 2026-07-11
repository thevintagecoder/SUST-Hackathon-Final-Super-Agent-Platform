"""Tests for synthetic anomaly ground-truth evaluation."""

from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.data_loading.synthetic_loader import (
    load_synthetic_scenario,
)
from backend.app.db.base import Base
from backend.app.evaluation.anomaly_evaluator import (
    evaluate_anomaly_scenarios,
)
from synthetic_data.generator import (
    generate_bundle,
)


def test_anomaly_evaluation_matches_ground_truth(
    tmp_path: Path,
) -> None:
    """Normal and repeated scenarios should classify correctly."""

    generated_directory = (
        tmp_path / "generated"
    )

    generate_bundle(
        output_directory=generated_directory,
        seed=42,
    )

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        load_synthetic_scenario(
            db=db,
            input_directory=(
                generated_directory
            ),
            scenario_id="NORMAL-001",
        )

        load_synthetic_scenario(
            db=db,
            input_directory=(
                generated_directory
            ),
            scenario_id="REPEATED-001",
        )

        result = evaluate_anomaly_scenarios(
            db=db,
            ground_truth_path=(
                generated_directory
                / "ground_truth.json"
            ),
            scenario_ids=(
                "NORMAL-001",
                "REPEATED-001",
            ),
        )

    assert result.true_positives == 1
    assert result.false_positives == 0
    assert result.true_negatives == 1
    assert result.false_negatives == 0

    assert (
        result.precision
        == Decimal("1.0000")
    )

    assert (
        result.recall
        == Decimal("1.0000")
    )

    assert (
        result.false_positive_rate
        == Decimal("0.0000")
    )

    assert result.passed is True

    normal_outcome = next(
        outcome
        for outcome in result.outcomes
        if (
            outcome.scenario_id
            == "NORMAL-001"
        )
    )

    repeated_outcome = next(
        outcome
        for outcome in result.outcomes
        if (
            outcome.scenario_id
            == "REPEATED-001"
        )
    )

    assert (
        normal_outcome.classification
        == "TRUE_NEGATIVE"
    )

    assert normal_outcome.passed is True

    assert (
        repeated_outcome.classification
        == "TRUE_POSITIVE"
    )

    assert repeated_outcome.passed is True

    engine.dispose()