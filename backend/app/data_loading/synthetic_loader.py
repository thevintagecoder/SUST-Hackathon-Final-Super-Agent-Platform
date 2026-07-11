"""Load one generated synthetic scenario into PostgreSQL."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.models import (
    Agent,
    AgentPosition,
    Provider,
    ProviderBalance,
    Transaction,
)


DEFAULT_INPUT_DIRECTORY = Path(
    "synthetic_data/generated/demo"
)
DEFAULT_SCENARIO_ID = "REPEATED-001"

REQUIRED_FILES = (
    "initial_positions.csv",
    "provider_balances.csv",
    "provider_feed_status.csv",
    "transactions.csv",
    "ground_truth.json",
)

PROVIDER_NAMES = {
    "BKASH_SIM": "Synthetic Provider BKASH",
    "NAGAD_SIM": "Synthetic Provider NAGAD",
    "ROCKET_SIM": "Synthetic Provider ROCKET",
}


@dataclass(frozen=True)
class LoadSummary:
    """Describe the result of one scenario load."""

    scenario_id: str
    agent_created: bool
    providers_created: int
    position_created: bool
    balances_created: int
    balances_updated: int
    transactions_inserted: int
    transactions_skipped: int


def read_csv_rows(
    path: Path,
) -> list[dict[str, str]]:
    """Read one generated CSV file."""

    with path.open(
        encoding="utf-8",
        newline="",
    ) as input_file:
        return list(csv.DictReader(input_file))


def validate_input_directory(
    input_directory: Path,
) -> None:
    """Ensure all required generated files exist."""

    missing_files = [
        filename
        for filename in REQUIRED_FILES
        if not (
            input_directory / filename
        ).is_file()
    ]

    if missing_files:
        missing_text = ", ".join(missing_files)

        raise FileNotFoundError(
            "Missing required synthetic-data files: "
            f"{missing_text}"
        )


def parse_datetime(
    value: str,
) -> datetime:
    """Parse a generated ISO-8601 datetime."""

    if not value:
        raise ValueError(
            "A required datetime value was empty."
        )

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def parse_optional_datetime(
    value: str,
) -> datetime | None:
    """Parse an optional generated datetime."""

    if not value:
        return None

    return parse_datetime(value)


def parse_decimal(
    value: str,
    *,
    allow_zero: bool,
) -> Decimal:
    """Parse and validate one generated money value."""

    try:
        parsed_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(
            f"Invalid monetary value: {value}"
        ) from exc

    if allow_zero:
        valid = parsed_value >= 0
    else:
        valid = parsed_value > 0

    if not valid:
        raise ValueError(
            f"Invalid monetary value: {value}"
        )

    return parsed_value


def parse_boolean(
    value: str,
) -> bool:
    """Parse a generated lowercase boolean."""

    normalized_value = value.strip().lower()

    if normalized_value == "true":
        return True

    if normalized_value == "false":
        return False

    raise ValueError(
        f"Invalid boolean value: {value}"
    )


def rows_for_scenario(
    rows: list[dict[str, str]],
    scenario_id: str,
) -> list[dict[str, str]]:
    """Filter generated rows by scenario identifier."""

    return [
        row
        for row in rows
        if row.get("scenario_id") == scenario_id
    ]


def get_or_create_agent(
    db: Session,
    agent_code: str,
) -> tuple[Agent, bool]:
    """Return the synthetic Agent, creating it when absent."""

    agent = db.scalar(
        select(Agent).where(
            Agent.code == agent_code
        )
    )

    if agent is not None:
        return agent, False

    agent = Agent(
        code=agent_code,
        name="Synthetic Sylhet Agent",
        area="Sylhet",
    )

    db.add(agent)
    db.flush()

    return agent, True


def get_or_create_provider(
    db: Session,
    provider_code: str,
) -> tuple[Provider, bool]:
    """Return one synthetic provider."""

    if provider_code not in PROVIDER_NAMES:
        raise ValueError(
            "Unsupported synthetic provider: "
            f"{provider_code}"
        )

    provider = db.scalar(
        select(Provider).where(
            Provider.code == provider_code
        )
    )

    if provider is not None:
        return provider, False

    provider = Provider(
        code=provider_code,
        name=PROVIDER_NAMES[provider_code],
    )

    db.add(provider)
    db.flush()

    return provider, True


def load_synthetic_scenario(
    db: Session,
    input_directory: Path,
    scenario_id: str,
) -> LoadSummary:
    """Load one generated scenario into the database."""

    validate_input_directory(input_directory)

    initial_position_rows = rows_for_scenario(
        read_csv_rows(
            input_directory
            / "initial_positions.csv"
        ),
        scenario_id,
    )
    provider_balance_rows = rows_for_scenario(
        read_csv_rows(
            input_directory
            / "provider_balances.csv"
        ),
        scenario_id,
    )
    provider_feed_rows = rows_for_scenario(
        read_csv_rows(
            input_directory
            / "provider_feed_status.csv"
        ),
        scenario_id,
    )
    transaction_rows = rows_for_scenario(
        read_csv_rows(
            input_directory
            / "transactions.csv"
        ),
        scenario_id,
    )

    if len(initial_position_rows) != 1:
        raise ValueError(
            "Expected exactly one initial position "
            f"for scenario {scenario_id}."
        )

    if not provider_balance_rows:
        raise ValueError(
            "No provider balances found for scenario "
            f"{scenario_id}."
        )

    if not transaction_rows:
        raise ValueError(
            "No transactions found for scenario "
            f"{scenario_id}."
        )

    feed_state_by_provider = {
        row["provider_code"]: row
        for row in provider_feed_rows
    }

    position_row = initial_position_rows[0]
    agent_code = position_row["agent_code"]

    providers_created = 0
    balances_created = 0
    balances_updated = 0
    transactions_inserted = 0
    transactions_skipped = 0

    try:
        agent, agent_created = get_or_create_agent(
            db,
            agent_code,
        )

        provider_by_code: dict[str, Provider] = {}

        for balance_row in provider_balance_rows:
            provider_code = balance_row[
                "provider_code"
            ]

            provider, provider_created = (
                get_or_create_provider(
                    db,
                    provider_code,
                )
            )

            provider_by_code[provider_code] = provider

            if provider_created:
                providers_created += 1

        position = db.scalar(
            select(AgentPosition).where(
                AgentPosition.agent_id == agent.id
            )
        )

        position_created = position is None

        if position is None:
            position = AgentPosition(
                agent_id=agent.id,
                shared_cash=parse_decimal(
                    position_row["shared_cash"],
                    allow_zero=True,
                ),
                as_of=parse_datetime(
                    position_row["as_of"]
                ),
            )
            db.add(position)
        else:
            position.shared_cash = parse_decimal(
                position_row["shared_cash"],
                allow_zero=True,
            )
            position.as_of = parse_datetime(
                position_row["as_of"]
            )

        for balance_row in provider_balance_rows:
            provider_code = balance_row[
                "provider_code"
            ]
            provider = provider_by_code[
                provider_code
            ]

            feed_row = feed_state_by_provider.get(
                provider_code
            )

            if feed_row is None:
                raise ValueError(
                    "Missing provider-feed row for "
                    f"{provider_code}."
                )

            if (
                feed_row["freshness_state"]
                != balance_row["freshness_state"]
            ):
                raise ValueError(
                    "Provider freshness mismatch for "
                    f"{provider_code}."
                )

            balance = db.scalar(
                select(ProviderBalance).where(
                    ProviderBalance.agent_id
                    == agent.id,
                    ProviderBalance.provider_id
                    == provider.id,
                )
            )

            electronic_balance = parse_decimal(
                balance_row["electronic_balance"],
                allow_zero=True,
            )
            last_update_at = parse_datetime(
                balance_row["last_update_at"]
            )
            freshness_state = balance_row[
                "freshness_state"
            ]

            if balance is None:
                balance = ProviderBalance(
                    agent_id=agent.id,
                    provider_id=provider.id,
                    electronic_balance=(
                        electronic_balance
                    ),
                    last_update_at=last_update_at,
                    freshness_state=freshness_state,
                )
                db.add(balance)
                balances_created += 1
            else:
                balance.electronic_balance = (
                    electronic_balance
                )
                balance.last_update_at = (
                    last_update_at
                )
                balance.freshness_state = (
                    freshness_state
                )
                balances_updated += 1

        external_ids = [
            row["external_id"]
            for row in transaction_rows
        ]

        existing_external_ids = set(
            db.scalars(
                select(Transaction.external_id).where(
                    Transaction.external_id.in_(
                        external_ids
                    )
                )
            ).all()
        )

        for transaction_row in transaction_rows:
            external_id = transaction_row[
                "external_id"
            ]

            if external_id in existing_external_ids:
                transactions_skipped += 1
                continue

            provider_code = transaction_row[
                "provider_code"
            ]

            provider = provider_by_code.get(
                provider_code
            )

            if provider is None:
                provider, provider_created = (
                    get_or_create_provider(
                        db,
                        provider_code,
                    )
                )
                provider_by_code[
                    provider_code
                ] = provider

                if provider_created:
                    providers_created += 1

            transaction = Transaction(
                external_id=external_id,
                scenario_id=transaction_row[
                    "scenario_id"
                ],
                agent_id=agent.id,
                provider_id=provider.id,
                synthetic_customer_id=(
                    transaction_row[
                        "synthetic_customer_id"
                    ]
                ),
                transaction_type=transaction_row[
                    "transaction_type"
                ],
                amount=parse_decimal(
                    transaction_row["amount"],
                    allow_zero=False,
                ),
                occurred_at=parse_datetime(
                    transaction_row["occurred_at"]
                ),
                status=transaction_row["status"],
                anomaly_expected=parse_boolean(
                    transaction_row[
                        "anomaly_expected"
                    ]
                ),
                anomaly_category=(
                    transaction_row[
                        "anomaly_category"
                    ]
                    or None
                ),
                injection_start_time=(
                    parse_optional_datetime(
                        transaction_row[
                            "injection_start_time"
                        ]
                    )
                ),
            )

            db.add(transaction)
            transactions_inserted += 1

        db.commit()

    except Exception:
        db.rollback()
        raise

    return LoadSummary(
        scenario_id=scenario_id,
        agent_created=agent_created,
        providers_created=providers_created,
        position_created=position_created,
        balances_created=balances_created,
        balances_updated=balances_updated,
        transactions_inserted=(
            transactions_inserted
        ),
        transactions_skipped=transactions_skipped,
    )


def print_summary(
    summary: LoadSummary,
) -> None:
    """Print a readable loader result."""

    print("Synthetic scenario loaded successfully.")
    print(f"Scenario: {summary.scenario_id}")
    print(
        "Agent created: "
        f"{summary.agent_created}"
    )
    print(
        "Providers created: "
        f"{summary.providers_created}"
    )
    print(
        "Position created: "
        f"{summary.position_created}"
    )
    print(
        "Balances created: "
        f"{summary.balances_created}"
    )
    print(
        "Balances updated: "
        f"{summary.balances_updated}"
    )
    print(
        "Transactions inserted: "
        f"{summary.transactions_inserted}"
    )
    print(
        "Transactions skipped: "
        f"{summary.transactions_skipped}"
    )


def main() -> None:
    """Run the loader from the command line."""

    parser = argparse.ArgumentParser(
        description=(
            "Load one generated synthetic scenario "
            "into PostgreSQL."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_DIRECTORY,
    )
    parser.add_argument(
        "--scenario",
        default=DEFAULT_SCENARIO_ID,
    )

    arguments = parser.parse_args()

    with SessionLocal() as db:
        summary = load_synthetic_scenario(
            db=db,
            input_directory=arguments.input,
            scenario_id=arguments.scenario,
        )

    print_summary(summary)


if __name__ == "__main__":
    main()