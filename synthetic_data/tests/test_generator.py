"""Tests for the deterministic synthetic-data generator."""

import csv
import json
from pathlib import Path

from synthetic_data.generator import (
    generate_bundle,
)


EXPECTED_FILENAMES = {
    "agents.csv",
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


def test_agents_file_contains_four_synthetic_agents(
    tmp_path: Path,
) -> None:
    """The network should contain four located Agents."""

    generate_bundle(
        output_directory=tmp_path,
        seed=42,
    )

    rows = read_csv_rows(
        tmp_path / "agents.csv"
    )

    assert len(rows) == 4

    agent_codes = {
        row["agent_code"]
        for row in rows
    }

    assert agent_codes == {
        "AGENT-SYL-001",
        "AGENT-SYL-002",
        "AGENT-SYL-003",
        "AGENT-SYL-004",
    }

    for row in rows:
        assert row["agent_code"].startswith(
            "AGENT-SYL-"
        )
        assert row["area"] == "Sylhet"
        assert row["latitude"]
        assert row["longitude"]
        assert row["is_active"] == "true"


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
        assert row[
            "synthetic_customer_id"
        ].startswith(
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
    "NETWORK-001",
    "FORECAST-001",
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


def test_network_scenario_has_four_agent_positions(
    tmp_path: Path,
) -> None:
    """NETWORK-001 should contain all four Agents."""

    generate_bundle(
        output_directory=tmp_path,
        seed=42,
    )

    rows = read_csv_rows(
        tmp_path / "initial_positions.csv"
    )

    network_rows = [
        row
        for row in rows
        if row["scenario_id"] == "NETWORK-001"
    ]

    assert len(network_rows) == 4

    cash_by_agent = {
        row["agent_code"]: row["shared_cash"]
        for row in network_rows
    }

    assert (
        cash_by_agent["AGENT-SYL-001"]
        == "25000.00"
    )
    assert (
        cash_by_agent["AGENT-SYL-003"]
        == "140000.00"
    )


def test_network_scenario_has_expected_nagad_capacity(
    tmp_path: Path,
) -> None:
    """Agents should have different Nagad capabilities."""

    generate_bundle(
        output_directory=tmp_path,
        seed=42,
    )

    balance_rows = read_csv_rows(
        tmp_path / "provider_balances.csv"
    )

    nagad_rows = [
        row
        for row in balance_rows
        if (
            row["scenario_id"]
            == "NETWORK-001"
            and row["provider_code"]
            == "NAGAD_SIM"
        )
    ]

    balance_by_agent = {
        row["agent_code"]: row
        for row in nagad_rows
    }

    assert len(balance_by_agent) == 4

    assert (
        balance_by_agent[
            "AGENT-SYL-001"
        ]["electronic_balance"]
        == "20000.00"
    )
    assert (
        balance_by_agent[
            "AGENT-SYL-002"
        ]["electronic_balance"]
        == "120000.00"
    )
    assert (
        balance_by_agent[
            "AGENT-SYL-004"
        ]["electronic_balance"]
        == "150000.00"
    )
    assert (
        balance_by_agent[
            "AGENT-SYL-004"
        ]["freshness_state"]
        == "delayed"
    )


def test_network_ground_truth_describes_customer_request(
    tmp_path: Path,
) -> None:
    """Ground truth should record the expected network outcome."""

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

    network_scenario = next(
        scenario
        for scenario in ground_truth["scenarios"]
        if scenario["scenario_id"] == "NETWORK-001"
    )

    request = network_scenario[
        "serviceability_request"
    ]

    assert (
        request["requesting_agent_code"]
        == "AGENT-SYL-001"
    )
    assert request["provider_code"] == "NAGAD_SIM"
    assert request["requested_amount"] == "80000.00"
    assert request["expected_shortfall"] == "60000.00"
    assert (
        request["expected_local_serviceable"]
        is False
    )
    assert (
        request["preferred_fresh_candidate"]
        == "AGENT-SYL-002"
    )
    assert (
        request["cash_out_candidate"]
        == "AGENT-SYL-003"
    )
    assert (
        request["stale_candidate"]
        == "AGENT-SYL-004"
    )

def test_forecast_scenario_has_deterministic_ground_truth(
    tmp_path: Path,
) -> None:
    """FORECAST-001 should have reproducible evaluation values."""

    generate_bundle(
        output_directory=tmp_path,
        seed=42,
    )

    transaction_rows = read_csv_rows(
        tmp_path / "transactions.csv"
    )

    forecast_rows = [
        row
        for row in transaction_rows
        if (
            row["scenario_id"]
            == "FORECAST-001"
        )
    ]

    assert len(forecast_rows) == 6

    assert all(
        row["agent_code"]
        == "AGENT-SYL-001"
        for row in forecast_rows
    )

    assert all(
        row["provider_code"]
        == "NAGAD_SIM"
        for row in forecast_rows
    )

    cash_in_total = sum(
        float(row["amount"])
        for row in forecast_rows
        if row["transaction_type"]
        == "cash_in"
    )

    cash_out_total = sum(
        float(row["amount"])
        for row in forecast_rows
        if row["transaction_type"]
        == "cash_out"
    )

    assert cash_in_total == 50000.00
    assert cash_out_total == 5000.00

    ground_truth = json.loads(
        (
            tmp_path / "ground_truth.json"
        ).read_text(
            encoding="utf-8",
        )
    )

    forecast_scenario = next(
        scenario
        for scenario in ground_truth[
            "scenarios"
        ]
        if (
            scenario["scenario_id"]
            == "FORECAST-001"
        )
    )

    evaluation = forecast_scenario[
        "forecast_evaluation"
    ]

    assert (
        evaluation[
            "expected_runway_hours"
        ]
        == "8.00"
    )
    assert (
        evaluation[
            "expected_risk_level"
        ]
        == "HIGH"
    )
    assert (
        evaluation[
            "expected_forecast_error_hours"
        ]
        == "0.50"
    )
    assert (
        evaluation[
            "expected_warning_lead_time_hours"
        ]
        == "8.50"
    )