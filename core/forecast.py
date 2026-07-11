"""Liquidity forecasting for provider e-float balances.

Semantics of the synthetic data: a customer cash_in hands physical cash
to the agent, so the agent's electronic float for that provider goes
DOWN. A cash_out does the opposite. Forecasts are simple linear runway
projections from the recent net outflow rate — decision support, not a
guarantee.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pandas as pd

from core.data_access import DemoDataRepository

DEFAULT_HORIZON_HOURS = 12
DEFAULT_WARNING_THRESHOLD_HOURS = 6.0

# Confidence model: start high, subtract penalties for reduced evidence.
BASE_CONFIDENCE = 0.92
PENALTY_DELAYED_FEED = 0.25
PENALTY_STALE_FEED = 0.40
PENALTY_SMALL_SAMPLE = 0.15
PENALTY_HIGH_VOLATILITY = 0.10
SMALL_SAMPLE_SIZE = 6
HIGH_VOLATILITY_THRESHOLD = 0.75
MIN_CONFIDENCE = 0.05
MAX_CONFIDENCE = 0.95


@dataclass
class ProviderForecast:
    """Forecast result for one provider float."""

    provider_code: str
    freshness: str
    current_balance: float
    net_outflow_per_hour: float
    runway_hours: float  # math.inf when the balance is not draining
    warning_threshold_hours: float
    confidence: float
    sample_size: int
    window_hours: float
    volatility: float
    as_of: datetime
    projected_low_time: datetime | None
    timeline: pd.DataFrame = field(repr=False)  # columns: time, balance, kind

    @property
    def is_below_warning(self) -> bool:
        return self.runway_hours < self.warning_threshold_hours


def _signed_flows(transactions: pd.DataFrame) -> pd.Series:
    """Return signed e-float deltas (cash_in drains, cash_out refills)."""

    signs = transactions["transaction_type"].map(
        {"cash_in": -1.0, "cash_out": 1.0}
    )
    return transactions["amount"] * signs


def _compute_confidence(
    freshness: str,
    sample_size: int,
    volatility: float,
) -> float:
    confidence = BASE_CONFIDENCE
    if freshness == "delayed":
        confidence -= PENALTY_DELAYED_FEED
    elif freshness == "stale":
        confidence -= PENALTY_STALE_FEED
    if sample_size < SMALL_SAMPLE_SIZE:
        confidence -= PENALTY_SMALL_SAMPLE
    if volatility > HIGH_VOLATILITY_THRESHOLD:
        confidence -= PENALTY_HIGH_VOLATILITY
    return max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, confidence))


def forecast_provider(
    repository: DemoDataRepository,
    scenario_id: str,
    agent_code: str,
    provider_code: str,
    horizon_hours: int = DEFAULT_HORIZON_HOURS,
    warning_threshold_hours: float = DEFAULT_WARNING_THRESHOLD_HOURS,
) -> ProviderForecast:
    """Forecast one provider float from the scenario transaction history."""

    balances = repository.balances_for(scenario_id, agent_code)
    balance_rows = balances.loc[balances["provider_code"] == provider_code]
    if balance_rows.empty:
        raise ValueError(
            f"No balance snapshot for provider '{provider_code}' in "
            f"scenario '{scenario_id}'."
        )
    snapshot = balance_rows.iloc[0]
    starting_balance = float(snapshot["electronic_balance"])
    freshness = str(snapshot["freshness_state"])

    transactions = repository.transactions_for(
        scenario_id,
        agent_code,
        provider_code,
    )

    scenario_transactions = repository.transactions_for(scenario_id, agent_code)
    if scenario_transactions.empty:
        now = snapshot["last_update_at"].to_pydatetime()
    else:
        now = scenario_transactions["occurred_at"].max().to_pydatetime()

    if transactions.empty:
        timeline = pd.DataFrame(
            {
                "time": [now],
                "balance": [starting_balance],
                "kind": ["history"],
            }
        )
        confidence = _compute_confidence(freshness, 0, 0.0)
        return ProviderForecast(
            provider_code=provider_code,
            freshness=freshness,
            current_balance=starting_balance,
            net_outflow_per_hour=0.0,
            runway_hours=math.inf,
            warning_threshold_hours=warning_threshold_hours,
            confidence=confidence,
            sample_size=0,
            window_hours=0.0,
            volatility=0.0,
            as_of=now,
            projected_low_time=None,
            timeline=timeline,
        )

    flows = _signed_flows(transactions)
    history = pd.DataFrame(
        {
            "time": transactions["occurred_at"],
            "balance": starting_balance + flows.cumsum(),
            "kind": "history",
        }
    )
    current_balance = float(history["balance"].iloc[-1])

    window_start = transactions["occurred_at"].min()
    window_hours = max(
        (transactions["occurred_at"].max() - window_start).total_seconds()
        / 3600.0,
        0.25,
    )
    net_outflow_per_hour = float(-flows.sum()) / window_hours

    hourly = (
        pd.DataFrame({"occurred_at": transactions["occurred_at"], "flow": flows})
        .set_index("occurred_at")
        .resample("1h")["flow"]
        .sum()
    )
    mean_abs_flow = float(hourly.abs().mean())
    volatility = (
        float(hourly.std(ddof=0)) / mean_abs_flow if mean_abs_flow > 0 else 0.0
    )

    if net_outflow_per_hour > 0:
        runway_hours = current_balance / net_outflow_per_hour
    else:
        runway_hours = math.inf

    forecast_points = []
    for hour in range(1, horizon_hours + 1):
        projected = max(current_balance - net_outflow_per_hour * hour, 0.0)
        forecast_points.append(
            {
                "time": now + timedelta(hours=hour),
                "balance": projected,
                "kind": "forecast",
            }
        )
    timeline = pd.concat(
        [history, pd.DataFrame(forecast_points)],
        ignore_index=True,
    )

    projected_low_time = (
        now + timedelta(hours=runway_hours)
        if math.isfinite(runway_hours)
        else None
    )

    confidence = _compute_confidence(freshness, len(transactions), volatility)

    return ProviderForecast(
        provider_code=provider_code,
        freshness=freshness,
        current_balance=current_balance,
        net_outflow_per_hour=net_outflow_per_hour,
        runway_hours=runway_hours,
        warning_threshold_hours=warning_threshold_hours,
        confidence=confidence,
        sample_size=int(len(transactions)),
        window_hours=window_hours,
        volatility=volatility,
        as_of=now,
        projected_low_time=projected_low_time,
        timeline=timeline,
    )


def forecast_scenario(
    repository: DemoDataRepository,
    scenario_id: str,
    agent_code: str,
    horizon_hours: int = DEFAULT_HORIZON_HOURS,
    warning_threshold_hours: float = DEFAULT_WARNING_THRESHOLD_HOURS,
) -> list[ProviderForecast]:
    """Forecast every provider float for one agent in one scenario."""

    balances = repository.balances_for(scenario_id, agent_code)
    return [
        forecast_provider(
            repository,
            scenario_id,
            agent_code,
            provider_code,
            horizon_hours=horizon_hours,
            warning_threshold_hours=warning_threshold_hours,
        )
        for provider_code in sorted(balances["provider_code"].unique())
    ]
