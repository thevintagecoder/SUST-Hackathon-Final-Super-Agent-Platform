"""Tests for deterministic runway forecast evaluation."""

from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.data_loading.synthetic_loader import (
    load_synthetic_scenario,
)
from backend.app.db.base import Base
from backend.app.evaluation.forecast_evaluator import (
    evaluate_forecast_scenario,
)
from synthetic_data.generator import (
    generate_bundle,
)


def test_forecast_evaluation_matches_ground_truth(
    tmp_path: Path,
) -> None:
    """Evaluate FORECAST-001 against known outcomes."""

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
            scenario_id="FORECAST-001",
        )

        result = evaluate_forecast_scenario(
            db=db,
            ground_truth_path=(
                generated_directory
                / "ground_truth.json"
            ),
            scenario_id="FORECAST-001",
        )

    assert result.predicted_risk_level == "HIGH"
    assert result.expected_risk_level == "HIGH"

    assert (
        result.predicted_runway_hours
        == Decimal("8.00")
    )

    assert (
        result.forecast_error_hours
        == Decimal("0.50")
    )

    assert (
        result.shortage_warning_lead_time_hours
        == Decimal("8.50")
    )

    assert result.warning_triggered is True
    assert result.passed is True

    engine.dispose()