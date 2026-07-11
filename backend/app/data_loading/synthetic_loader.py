"""Load one generated synthetic scenario into PostgreSQL."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

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
DEFAULT_SCENARIO_ID = "NETWORK-001"

REQUIRED_FILES = (
    "agents.csv",
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
    agents_created: int
    agents_updated: int
    providers_created: int
    positions_created: int
    positions_updated: int
    balances_created: int
    balances_updated: int
    transactions_inserted: int
    transactions_skipped: int

    @property
    def agent_created(self) -> bool:
        """Preserve compatibility with earlier single-Agent tests."""

        return self.agents_created > 0

    @property
    def position_created(self) -> bool:
        """Preserve compatibility with earlier single-Agent tests."""

        return self.positions_created > 0


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
    """Parse and validate one generated monetary value."""

    try:
        parsed_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(
            f"Invalid monetary value: {value}"
        ) from exc

    valid = (
        parsed_value >= 0
        if allow_zero
        else parsed_value > 0
    )

    if not valid:
        raise ValueError(
            f"Invalid monetary value: {value}"
        )

    return parsed_value


def parse_optional_decimal(
    value: str,
) -> Decimal | None:
    """Parse an optional decimal such as a coordinate."""

    if not value:
        return None

    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(
            f"Invalid decimal value: {value}"
        ) from exc


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


def index_agent_rows(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Index unique generated Agent rows by code."""

    indexed_rows: dict[
        str,
        dict[str, str],
    ] = {}

    for row in rows:
        agent_code = row["agent_code"]

        if agent_code in indexed_rows:
            raise ValueError(
                "Duplicate Agent definition found: "
                f"{agent_code}"
            )

        indexed_rows[agent_code] = row

    return indexed_rows


def get_or_create_agent(
    db: Session,
    agent_row: dict[str, str],
) -> tuple[Agent, bool]:
    """Create or update one synthetic Agent."""

    agent_code = agent_row["agent_code"]

    agent = db.scalar(
        select(Agent).where(
            Agent.code == agent_code
        )
    )

    latitude = parse_optional_decimal(
        agent_row["latitude"]
    )
    longitude = parse_optional_decimal(
        agent_row["longitude"]
    )
    is_active = parse_boolean(
        agent_row["is_active"]
    )

    if agent is not None:
        agent.name = agent_row["name"]
        agent.area = agent_row["area"]
        agent.latitude = latitude
        agent.longitude = longitude
        agent.is_active = is_active

        return agent, False

    agent = Agent(
        code=agent_code,
        name=agent_row["name"],
        area=agent_row["area"],
        latitude=latitude,
        longitude=longitude,
        is_active=is_active,
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

    all_agent_rows = read_csv_rows(
        input_directory / "agents.csv"
    )
    agent_definition_by_code = (
        index_agent_rows(all_agent_rows)
    )

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

    if not initial_position_rows:
        raise ValueError(
            "Expected exactly one initial position for a "
            "single-Agent scenario or multiple positions for "
            f"a network scenario; none found for {scenario_id}."
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

    position_row_by_agent: dict[
        str,
        dict[str, str],
    ] = {}

    for row in initial_position_rows:
        agent_code = row["agent_code"]

        if agent_code in position_row_by_agent:
            raise ValueError(
                "Duplicate initial position found for "
                f"{agent_code} in {scenario_id}."
            )

        position_row_by_agent[agent_code] = row

    scenario_agent_codes = set(
        position_row_by_agent
    )

    for agent_code in scenario_agent_codes:
        if agent_code not in agent_definition_by_code:
            raise ValueError(
                "Missing Agent definition for "
                f"{agent_code}."
            )

    expected_balance_keys = {
        (
            agent_code,
            provider_code,
        )
        for agent_code in scenario_agent_codes
        for provider_code in PROVIDER_NAMES
    }

    actual_balance_keys: set[
        tuple[str, str]
    ] = set()

    for row in provider_balance_rows:
        key = (
            row["agent_code"],
            row["provider_code"],
        )

        if key in actual_balance_keys:
            raise ValueError(
                "Duplicate provider balance found for "
                f"{key[0]} and {key[1]}."
            )

        actual_balance_keys.add(key)

    if actual_balance_keys != expected_balance_keys:
        missing_keys = (
            expected_balance_keys
            - actual_balance_keys
        )
        extra_keys = (
            actual_balance_keys
            - expected_balance_keys
        )

        raise ValueError(
            "Provider-balance coverage mismatch. "
            f"Missing: {sorted(missing_keys)}. "
            f"Unexpected: {sorted(extra_keys)}."
        )

    feed_row_by_key: dict[
        tuple[str, str],
        dict[str, str],
    ] = {}

    for row in provider_feed_rows:
        key = (
            row["agent_code"],
            row["provider_code"],
        )

        if key in feed_row_by_key:
            raise ValueError(
                "Duplicate provider-feed row found for "
                f"{key[0]} and {key[1]}."
            )

        feed_row_by_key[key] = row

    if set(feed_row_by_key) != expected_balance_keys:
        raise ValueError(
            "Provider-feed rows do not cover every "
            "Agent-provider balance."
        )

    agents_created = 0
    agents_updated = 0
    providers_created = 0
    positions_created = 0
    positions_updated = 0
    balances_created = 0
    balances_updated = 0
    transactions_inserted = 0
    transactions_skipped = 0

    try:
        agent_by_code: dict[str, Agent] = {}

        for agent_code in sorted(
            scenario_agent_codes
        ):
            agent, created = get_or_create_agent(
                db=db,
                agent_row=(
                    agent_definition_by_code[
                        agent_code
                    ]
                ),
            )

            agent_by_code[agent_code] = agent

            if created:
                agents_created += 1
            else:
                agents_updated += 1

        provider_by_code: dict[
            str,
            Provider,
        ] = {}

        for provider_code in sorted(
            PROVIDER_NAMES
        ):
            provider, created = (
                get_or_create_provider(
                    db=db,
                    provider_code=provider_code,
                )
            )

            provider_by_code[
                provider_code
            ] = provider

            if created:
                providers_created += 1

        for agent_code in sorted(
            scenario_agent_codes
        ):
            agent = agent_by_code[
                agent_code
            ]
            position_row = (
                position_row_by_agent[
                    agent_code
                ]
            )

            position = db.scalar(
                select(AgentPosition).where(
                    AgentPosition.agent_id
                    == agent.id
                )
            )

            shared_cash = parse_decimal(
                position_row["shared_cash"],
                allow_zero=True,
            )
            as_of = parse_datetime(
                position_row["as_of"]
            )

            if position is None:
                position = AgentPosition(
                    agent_id=agent.id,
                    shared_cash=shared_cash,
                    as_of=as_of,
                )
                db.add(position)
                positions_created += 1
            else:
                position.shared_cash = shared_cash
                position.as_of = as_of
                positions_updated += 1

        for balance_row in provider_balance_rows:
            agent_code = balance_row[
                "agent_code"
            ]
            provider_code = balance_row[
                "provider_code"
            ]

            agent = agent_by_code.get(
                agent_code
            )
            provider = provider_by_code.get(
                provider_code
            )

            if agent is None:
                raise ValueError(
                    "Provider balance references an "
                    f"unknown Agent: {agent_code}"
                )

            if provider is None:
                raise ValueError(
                    "Provider balance references an "
                    f"unknown provider: {provider_code}"
                )

            feed_key = (
                agent_code,
                provider_code,
            )
            feed_row = feed_row_by_key[
                feed_key
            ]

            if (
                feed_row["freshness_state"]
                != balance_row[
                    "freshness_state"
                ]
            ):
                raise ValueError(
                    "Provider freshness mismatch for "
                    f"{agent_code} and {provider_code}."
                )

            if (
                feed_row["last_update_at"]
                != balance_row[
                    "last_update_at"
                ]
            ):
                raise ValueError(
                    "Provider update-time mismatch for "
                    f"{agent_code} and {provider_code}."
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
                balance_row[
                    "electronic_balance"
                ],
                allow_zero=True,
            )
            last_update_at = parse_datetime(
                balance_row[
                    "last_update_at"
                ]
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
                    last_update_at=(
                        last_update_at
                    ),
                    freshness_state=(
                        freshness_state
                    ),
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
                select(
                    Transaction.external_id
                ).where(
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

            agent_code = transaction_row[
                "agent_code"
            ]
            provider_code = transaction_row[
                "provider_code"
            ]

            agent = agent_by_code.get(
                agent_code
            )
            provider = provider_by_code.get(
                provider_code
            )

            if agent is None:
                raise ValueError(
                    "Transaction references an unknown "
                    f"scenario Agent: {agent_code}"
                )

            if provider is None:
                raise ValueError(
                    "Transaction references an unknown "
                    f"provider: {provider_code}"
                )

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
                transaction_type=(
                    transaction_row[
                        "transaction_type"
                    ]
                ),
                amount=parse_decimal(
                    transaction_row["amount"],
                    allow_zero=False,
                ),
                occurred_at=parse_datetime(
                    transaction_row[
                        "occurred_at"
                    ]
                ),
                status=transaction_row[
                    "status"
                ],
                anomaly_expected=(
                    parse_boolean(
                        transaction_row[
                            "anomaly_expected"
                        ]
                    )
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
        agents_created=agents_created,
        agents_updated=agents_updated,
        providers_created=providers_created,
        positions_created=positions_created,
        positions_updated=positions_updated,
        balances_created=balances_created,
        balances_updated=balances_updated,
        transactions_inserted=(
            transactions_inserted
        ),
        transactions_skipped=(
            transactions_skipped
        ),
    )


def print_summary(
    summary: LoadSummary,
) -> None:
    """Print a readable loader result."""

    print(
        "Synthetic scenario loaded successfully."
    )
    print(
        f"Scenario: {summary.scenario_id}"
    )
    print(
        "Agents created: "
        f"{summary.agents_created}"
    )
    print(
        "Agents updated: "
        f"{summary.agents_updated}"
    )
    print(
        "Providers created: "
        f"{summary.providers_created}"
    )
    print(
        "Positions created: "
        f"{summary.positions_created}"
    )
    print(
        "Positions updated: "
        f"{summary.positions_updated}"
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