"""Read access to the deterministic synthetic demo dataset.

All dashboard analytics consume data through :class:`DemoDataRepository`
so pages never parse CSV files themselves. The repository is scenario
aware: every query is filtered to one scenario_id so the dashboard can
switch between the demo storylines (normal, shortage, repeated amounts,
stale feed).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "synthetic_data" / "generated" / "demo"


class DataUnavailableError(Exception):
    """Raised when the synthetic dataset is missing or incomplete."""


@dataclass(frozen=True)
class ScenarioInfo:
    """Ground-truth description of one demo scenario."""

    scenario_id: str
    name: str
    description: str
    anomaly_expected: bool
    anomaly_category: str | None
    expected_shortage_resource: str | None
    expected_shortage_time: str | None
    injection_start_time: str | None


class DemoDataRepository:
    """Load and filter the generated synthetic demo bundle."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or DEFAULT_DATA_DIR
        self._transactions: pd.DataFrame | None = None
        self._provider_balances: pd.DataFrame | None = None
        self._initial_positions: pd.DataFrame | None = None
        self._feed_status: pd.DataFrame | None = None
        self._ground_truth: dict | None = None

    def _read_csv(self, filename: str, parse_dates: list[str]) -> pd.DataFrame:
        path = self._data_dir / filename
        if not path.exists():
            raise DataUnavailableError(
                f"Synthetic data file '{filename}' was not found in "
                f"{self._data_dir}. Run the generator first: "
                "python -m synthetic_data.generator"
            )
        frame = pd.read_csv(path)
        for column in parse_dates:
            frame[column] = pd.to_datetime(frame[column], utc=True)
        return frame

    @property
    def transactions(self) -> pd.DataFrame:
        if self._transactions is None:
            frame = self._read_csv("transactions.csv", ["occurred_at"])
            frame["amount"] = frame["amount"].astype(float)
            self._transactions = frame
        return self._transactions

    @property
    def provider_balances(self) -> pd.DataFrame:
        if self._provider_balances is None:
            frame = self._read_csv("provider_balances.csv", ["last_update_at"])
            frame["electronic_balance"] = frame["electronic_balance"].astype(float)
            self._provider_balances = frame
        return self._provider_balances

    @property
    def initial_positions(self) -> pd.DataFrame:
        if self._initial_positions is None:
            frame = self._read_csv("initial_positions.csv", ["as_of"])
            frame["shared_cash"] = frame["shared_cash"].astype(float)
            self._initial_positions = frame
        return self._initial_positions

    @property
    def feed_status(self) -> pd.DataFrame:
        if self._feed_status is None:
            self._feed_status = self._read_csv(
                "provider_feed_status.csv",
                ["last_update_at"],
            )
        return self._feed_status

    @property
    def ground_truth(self) -> dict:
        if self._ground_truth is None:
            path = self._data_dir / "ground_truth.json"
            if not path.exists():
                raise DataUnavailableError(
                    f"ground_truth.json was not found in {self._data_dir}."
                )
            self._ground_truth = json.loads(path.read_text(encoding="utf-8"))
        return self._ground_truth

    def list_scenarios(self) -> list[ScenarioInfo]:
        return [
            ScenarioInfo(
                scenario_id=item["scenario_id"],
                name=item["name"],
                description=item["description"],
                anomaly_expected=item["anomaly_expected"],
                anomaly_category=item["anomaly_category"],
                expected_shortage_resource=item["expected_shortage_resource"],
                expected_shortage_time=item["expected_shortage_time"],
                injection_start_time=item["injection_start_time"],
            )
            for item in self.ground_truth["scenarios"]
        ]

    def list_agents(self, scenario_id: str) -> list[str]:
        frame = self.initial_positions
        agents = frame.loc[
            frame["scenario_id"] == scenario_id,
            "agent_code",
        ].unique()
        return sorted(agents)

    def list_providers(self) -> list[str]:
        return sorted(self.provider_balances["provider_code"].unique())

    def transactions_for(
        self,
        scenario_id: str,
        agent_code: str,
        provider_code: str | None = None,
    ) -> pd.DataFrame:
        frame = self.transactions
        mask = (frame["scenario_id"] == scenario_id) & (
            frame["agent_code"] == agent_code
        )
        if provider_code is not None:
            mask &= frame["provider_code"] == provider_code
        return frame.loc[mask].sort_values("occurred_at").reset_index(drop=True)

    def balances_for(self, scenario_id: str, agent_code: str) -> pd.DataFrame:
        frame = self.provider_balances
        mask = (frame["scenario_id"] == scenario_id) & (
            frame["agent_code"] == agent_code
        )
        return frame.loc[mask].reset_index(drop=True)

    def shared_cash_for(self, scenario_id: str, agent_code: str) -> float:
        frame = self.initial_positions
        mask = (frame["scenario_id"] == scenario_id) & (
            frame["agent_code"] == agent_code
        )
        rows = frame.loc[mask]
        if rows.empty:
            raise DataUnavailableError(
                f"No shared-cash position for agent '{agent_code}' in "
                f"scenario '{scenario_id}'."
            )
        return float(rows.iloc[0]["shared_cash"])

    def feed_status_for(self, scenario_id: str) -> pd.DataFrame:
        frame = self.feed_status
        return frame.loc[frame["scenario_id"] == scenario_id].reset_index(
            drop=True
        )
