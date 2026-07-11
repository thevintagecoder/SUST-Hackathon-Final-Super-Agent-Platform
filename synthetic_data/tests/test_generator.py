"""Tests for the deterministic synthetic-data generator."""

import csv
import json
from pathlib import Path

from synthetic_data.generator import (
    generate_bundle,
)


EXPECTED_FILENAMES = {
    "initial_positions.csv",
    "provider_balances.csv",
    "provider_feed_status.csv",
    "transactions.csv",
    "ground_truth.json",
}

ALLOWED_PROVIDERS = {
    "BKASH_SIM",
    "NAGAD_SIM",
    "ROCKET_SIM",
}

ALLOWED_TRANSACTION_TYPES = {
    "cash_in",
    "cash_out",
}


def read_csv_rows(
    path: Path,
) -> list[dict[str, str]]:
    """Read CSV content as dictionaries."""

    with path.open(
        encoding="utf-8",
        newline="",
    ) as input_file:
        return list(
            csv.DictReader(input_file)
        )


def test_generator_creates_expected_files(
    tmp_path: Path,
) -> None:
    """Generate every required output file."""

    generate_bundle(
        output_directory=tmp_path,
        seed=42,
    )

    generated_filenames = {
        path.name
        for path in tmp_path.iterdir()
        if path.is_file()
    }

    assert generated_filenames == (
        EXPECTED_FILENAMES
    )


def test_generator_is_reproducible(
    tmp_path: Path,
) -> None:
    """The same seed should produce identical files."""

    first_directory = tmp_path / "first"
    second_directory = tmp_path / "second"

    generate_bundle(
        output_directory=first_directory,
        seed=42,
    )
    generate_bundle(
        output_directory=second_directory,
        seed=42,
    )

    for filename in EXPECTED_FILENAMES:
        first_content = (
            first_directory / filename
        ).read_bytes()
        second_content = (
            second_directory / filename
        ).read_bytes()

        assert first_content == second_content


def test_transactions_are_valid(
    tmp_path: Path,
) -> None:
    """Generated transactions should follow the contract."""

    generate_bundle(
        output_directory=tmp_path,
        seed=42,
    )

    rows = read_csv_rows(
        tmp_path / "transactions.csv"
    )

    assert rows

    for row in rows:
        assert row["external_id"].startswith(
            "TXN-"
        )
        assert row["scenario_id"]
        assert row["agent_code"].startswith(
            "AGENT-"
        )
        assert (
            row["provider_code"]
            in ALLOWED_PROVIDERS
        )
        assert (
            row["transaction_type"]
            in ALLOWED_TRANSACTION_TYPES
        )
        assert float(row["amount"]) > 0
        assert row["synthetic_customer_id"].startswith(
            "CUSTOMER-"
        )


def test_ground_truth_contains_required_scenarios(
    tmp_path: Path,
) -> None:
    """Ground truth should identify all scenarios."""

    generate_bundle(
        output_directory=tmp_path,
        seed=42,
    )

    ground_truth = json.loads(
        (
            tmp_path / "ground_truth.json"
        ).read_text(
            encoding="utf-8",
        )
    )

    scenarios = {
        item["scenario_id"]: item
        for item in ground_truth["scenarios"]
    }

    assert set(scenarios) == {
        "NORMAL-001",
        "SHORTAGE-001",
        "REPEATED-001",
        "STALE-001",
    }

    assert (
        scenarios["NORMAL-001"][
            "anomaly_expected"
        ]
        is False
    )

    assert (
        scenarios["REPEATED-001"][
            "anomaly_expected"
        ]
        is True
    )

    assert (
        scenarios["REPEATED-001"][
            "anomaly_category"
        ]
        == "repeated_amounts"
    )

    assert (
        scenarios["SHORTAGE-001"][
            "expected_shortage_resource"
        ]
        == "BKASH_SIM"
    )


def test_repeated_scenario_contains_injected_rows(
    tmp_path: Path,
) -> None:
    """Injected repeated transactions should be labelled."""

    generate_bundle(
        output_directory=tmp_path,
        seed=42,
    )

    rows = read_csv_rows(
        tmp_path / "transactions.csv"
    )

    injected_rows = [
        row
        for row in rows
        if (
            row["scenario_id"]
            == "REPEATED-001"
            and row["anomaly_expected"]
            == "true"
        )
    ]

    assert len(injected_rows) == 5

    amounts = [
        float(row["amount"])
        for row in injected_rows
    ]

    assert amounts.count(5000.00) == 4
    assert 5050.00 in amounts


def test_stale_scenario_contains_delayed_feed(
    tmp_path: Path,
) -> None:
    """The stale scenario should contain delayed data."""

    generate_bundle(
        output_directory=tmp_path,
        seed=42,
    )

    rows = read_csv_rows(
        tmp_path / "provider_feed_status.csv"
    )

    delayed_rows = [
        row
        for row in rows
        if (
            row["scenario_id"]
            == "STALE-001"
            and row["provider_code"]
            == "ROCKET_SIM"
        )
    ]

    assert len(delayed_rows) == 1
    assert (
        delayed_rows[0]["freshness_state"]
        == "delayed"
    )