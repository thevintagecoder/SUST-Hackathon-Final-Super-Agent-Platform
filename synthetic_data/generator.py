"""Generate deterministic synthetic liquidity demonstration data."""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from synthetic_data.scenarios import (
    AGENT_CODE,
    BASE_TIME,
    PROVIDER_CODES,
    SCENARIOS,
    ScenarioDefinition,
)


DEFAULT_SEED = 42
DEFAULT_OUTPUT_DIRECTORY = Path(
    "synthetic_data/generated/demo"
)

TRANSACTION_FIELDS = (
    "external_id",
    "scenario_id",
    "agent_code",
    "provider_code",
    "synthetic_customer_id",
    "transaction_type",
    "amount",
    "occurred_at",
    "status",
    "anomaly_expected",
    "anomaly_category",
    "injection_start_time",
)

INITIAL_POSITION_FIELDS = (
    "scenario_id",
    "agent_code",
    "shared_cash",
    "as_of",
)

PROVIDER_BALANCE_FIELDS = (
    "scenario_id",
    "agent_code",
    "provider_code",
    "electronic_balance",
    "last_update_at",
    "freshness_state",
)

PROVIDER_FEED_FIELDS = (
    "scenario_id",
    "provider_code",
    "last_update_at",
    "freshness_state",
)


def format_datetime(value: datetime | None) -> str:
    """Return a stable ISO-8601 UTC representation."""

    if value is None:
        return ""

    utc_value = value.astimezone(UTC)

    return utc_value.isoformat().replace(
        "+00:00",
        "Z",
    )


def format_amount(value: float) -> str:
    """Format a synthetic monetary value with two decimals."""

    return f"{value:.2f}"


def write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, Any]],
) -> None:
    """Write deterministic CSV content."""

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def initial_balances_for_scenario(
    scenario_id: str,
) -> dict[str, float]:
    """Return scenario-specific starting provider balances."""

    if scenario_id == "SHORTAGE-001":
        return {
            "BKASH_SIM": 18000.00,
            "NAGAD_SIM": 72000.00,
            "ROCKET_SIM": 68000.00,
        }

    if scenario_id == "REPEATED-001":
        return {
            "BKASH_SIM": 26000.00,
            "NAGAD_SIM": 60000.00,
            "ROCKET_SIM": 58000.00,
        }

    return {
        "BKASH_SIM": 60000.00,
        "NAGAD_SIM": 62000.00,
        "ROCKET_SIM": 58000.00,
    }


def shared_cash_for_scenario(
    scenario_id: str,
) -> float:
    """Return scenario-specific starting shared cash."""

    if scenario_id == "SHORTAGE-001":
        return 70000.00

    if scenario_id == "REPEATED-001":
        return 65000.00

    return 50000.00


def feed_state_for_provider(
    scenario_id: str,
    provider_code: str,
) -> tuple[str, datetime]:
    """Return freshness state and update time."""

    if (
        scenario_id == "STALE-001"
        and provider_code == "ROCKET_SIM"
    ):
        return (
            "delayed",
            BASE_TIME - timedelta(hours=2),
        )

    return (
        "fresh",
        BASE_TIME,
    )


def normal_transaction_amount(
    random_generator: random.Random,
) -> float:
    """Return a normal synthetic transaction amount."""

    allowed_amounts = (
        500.00,
        1000.00,
        1500.00,
        2000.00,
        2500.00,
        3000.00,
        4000.00,
    )

    return random_generator.choice(
        allowed_amounts
    )


def create_standard_transactions(
    scenario: ScenarioDefinition,
    random_generator: random.Random,
    transaction_counter: int,
) -> tuple[list[dict[str, Any]], int]:
    """Generate ordinary activity for one scenario."""

    rows: list[dict[str, Any]] = []

    for index in range(24):
        provider_code = random_generator.choice(
            PROVIDER_CODES
        )
        transaction_type = random_generator.choice(
            ("cash_in", "cash_out")
        )

        if (
            scenario.scenario_id == "SHORTAGE-001"
            and index >= 10
        ):
            provider_code = "BKASH_SIM"
            transaction_type = "cash_in"

        occurred_at = BASE_TIME + timedelta(
            minutes=index * 15,
        )

        amount = normal_transaction_amount(
            random_generator
        )

        transaction_counter += 1

        rows.append(
            {
                "external_id": (
                    f"TXN-{transaction_counter:06d}"
                ),
                "scenario_id": scenario.scenario_id,
                "agent_code": AGENT_CODE,
                "provider_code": provider_code,
                "synthetic_customer_id": (
                    f"CUSTOMER-{index + 1:04d}"
                ),
                "transaction_type": transaction_type,
                "amount": format_amount(amount),
                "occurred_at": format_datetime(
                    occurred_at
                ),
                "status": "completed",
                "anomaly_expected": "false",
                "anomaly_category": "",
                "injection_start_time": (
                    format_datetime(
                        scenario.injection_start_time
                    )
                ),
            }
        )

    return rows, transaction_counter


def create_repeated_amount_transactions(
    scenario: ScenarioDefinition,
    transaction_counter: int,
) -> tuple[list[dict[str, Any]], int]:
    """Generate the injected repeated-amount sequence."""

    rows: list[dict[str, Any]] = []

    injection_start = (
        scenario.injection_start_time
        or BASE_TIME
    )

    repeated_amounts = (
        5000.00,
        5000.00,
        5000.00,
        5000.00,
        5050.00,
    )

    for index, amount in enumerate(
        repeated_amounts
    ):
        transaction_counter += 1

        occurred_at = injection_start + timedelta(
            minutes=index * 4,
        )

        rows.append(
            {
                "external_id": (
                    f"TXN-{transaction_counter:06d}"
                ),
                "scenario_id": scenario.scenario_id,
                "agent_code": AGENT_CODE,
                "provider_code": "BKASH_SIM",
                "synthetic_customer_id": (
                    f"CUSTOMER-REPEAT-{index + 1:02d}"
                ),
                "transaction_type": "cash_in",
                "amount": format_amount(amount),
                "occurred_at": format_datetime(
                    occurred_at
                ),
                "status": "completed",
                "anomaly_expected": "true",
                "anomaly_category": (
                    "repeated_amounts"
                ),
                "injection_start_time": (
                    format_datetime(
                        scenario.injection_start_time
                    )
                ),
            }
        )

    return rows, transaction_counter


def build_dataset(
    seed: int,
) -> dict[str, Any]:
    """Build all deterministic in-memory records."""

    random_generator = random.Random(seed)

    initial_position_rows: list[
        dict[str, Any]
    ] = []
    provider_balance_rows: list[
        dict[str, Any]
    ] = []
    provider_feed_rows: list[
        dict[str, Any]
    ] = []
    transaction_rows: list[
        dict[str, Any]
    ] = []
    ground_truth_scenarios: list[
        dict[str, Any]
    ] = []

    transaction_counter = 0

    for scenario in SCENARIOS:
        initial_position_rows.append(
            {
                "scenario_id": (
                    scenario.scenario_id
                ),
                "agent_code": AGENT_CODE,
                "shared_cash": format_amount(
                    shared_cash_for_scenario(
                        scenario.scenario_id
                    )
                ),
                "as_of": format_datetime(
                    BASE_TIME
                ),
            }
        )

        balances = initial_balances_for_scenario(
            scenario.scenario_id
        )

        for provider_code in PROVIDER_CODES:
            (
                freshness_state,
                last_update_at,
            ) = feed_state_for_provider(
                scenario.scenario_id,
                provider_code,
            )

            provider_balance_rows.append(
                {
                    "scenario_id": (
                        scenario.scenario_id
                    ),
                    "agent_code": AGENT_CODE,
                    "provider_code": provider_code,
                    "electronic_balance": (
                        format_amount(
                            balances[
                                provider_code
                            ]
                        )
                    ),
                    "last_update_at": (
                        format_datetime(
                            last_update_at
                        )
                    ),
                    "freshness_state": (
                        freshness_state
                    ),
                }
            )

            provider_feed_rows.append(
                {
                    "scenario_id": (
                        scenario.scenario_id
                    ),
                    "provider_code": provider_code,
                    "last_update_at": (
                        format_datetime(
                            last_update_at
                        )
                    ),
                    "freshness_state": (
                        freshness_state
                    ),
                }
            )

        (
            ordinary_rows,
            transaction_counter,
        ) = create_standard_transactions(
            scenario=scenario,
            random_generator=random_generator,
            transaction_counter=(
                transaction_counter
            ),
        )

        transaction_rows.extend(
            ordinary_rows
        )

        if scenario.anomaly_expected:
            (
                injected_rows,
                transaction_counter,
            ) = create_repeated_amount_transactions(
                scenario=scenario,
                transaction_counter=(
                    transaction_counter
                ),
            )

            transaction_rows.extend(
                injected_rows
            )

        ground_truth_scenarios.append(
            {
                "scenario_id": (
                    scenario.scenario_id
                ),
                "name": scenario.name,
                "description": (
                    scenario.description
                ),
                "anomaly_expected": (
                    scenario.anomaly_expected
                ),
                "anomaly_category": (
                    scenario.anomaly_category
                ),
                "expected_shortage_resource": (
                    scenario.expected_shortage_resource
                ),
                "injection_start_time": (
                    format_datetime(
                        scenario.injection_start_time
                    )
                    or None
                ),
                "expected_shortage_time": (
                    format_datetime(
                        scenario.expected_shortage_time
                    )
                    or None
                ),
            }
        )

    transaction_rows.sort(
        key=lambda row: (
            row["scenario_id"],
            row["occurred_at"],
            row["external_id"],
        )
    )

    return {
        "initial_positions": initial_position_rows,
        "provider_balances": provider_balance_rows,
        "provider_feed_status": provider_feed_rows,
        "transactions": transaction_rows,
        "ground_truth": {
            "seed": seed,
            "generated_at": format_datetime(
                BASE_TIME
            ),
            "agent_code": AGENT_CODE,
            "providers": list(
                PROVIDER_CODES
            ),
            "scenarios": ground_truth_scenarios,
        },
    }


def generate_bundle(
    output_directory: Path,
    seed: int = DEFAULT_SEED,
) -> dict[str, Path]:
    """Generate the complete demonstration bundle."""

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataset = build_dataset(seed)

    output_paths = {
        "initial_positions": (
            output_directory
            / "initial_positions.csv"
        ),
        "provider_balances": (
            output_directory
            / "provider_balances.csv"
        ),
        "provider_feed_status": (
            output_directory
            / "provider_feed_status.csv"
        ),
        "transactions": (
            output_directory
            / "transactions.csv"
        ),
        "ground_truth": (
            output_directory
            / "ground_truth.json"
        ),
    }

    write_csv(
        output_paths["initial_positions"],
        INITIAL_POSITION_FIELDS,
        dataset["initial_positions"],
    )

    write_csv(
        output_paths["provider_balances"],
        PROVIDER_BALANCE_FIELDS,
        dataset["provider_balances"],
    )

    write_csv(
        output_paths["provider_feed_status"],
        PROVIDER_FEED_FIELDS,
        dataset["provider_feed_status"],
    )

    write_csv(
        output_paths["transactions"],
        TRANSACTION_FIELDS,
        dataset["transactions"],
    )

    output_paths["ground_truth"].write_text(
        json.dumps(
            dataset["ground_truth"],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return output_paths


def main() -> None:
    """Run the generator from the command line."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic synthetic "
            "liquidity data."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
    )

    arguments = parser.parse_args()

    generated_paths = generate_bundle(
        output_directory=arguments.output,
        seed=arguments.seed,
    )

    print(
        "Synthetic data generated successfully."
    )

    for name, path in generated_paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()