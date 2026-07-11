"""Rule-based unusual-activity detection over synthetic transactions.

Every flag carries its evidence (the actual transactions), a confidence
between 0 and 1, and a recommended next step. Flags describe *unusual
activity for human review* — they never declare fraud.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from core.data_access import DemoDataRepository

REPEAT_WINDOW_MINUTES = 60
REPEAT_MIN_COUNT = 4
REPEAT_AMOUNT_TOLERANCE = 0.02  # amounts within 2% count as "repeated"

VELOCITY_RECENT_WINDOW_MINUTES = 60
VELOCITY_RATIO_THRESHOLD = 2.0


@dataclass
class AnomalyFlag:
    """One reviewable unusual-activity flag with its evidence."""

    flag_id: str
    category: str  # "repeated_amounts" | "velocity_spike"
    severity: str  # "high" | "medium" | "low"
    provider_code: str
    title: str
    reason: str
    confidence: float
    uncertainty: str
    recommended_next_step: str
    evidence: pd.DataFrame = field(repr=False)
    metrics: dict = field(default_factory=dict)


def _detect_repeated_amounts(
    transactions: pd.DataFrame,
    scenario_id: str,
) -> list[AnomalyFlag]:
    flags: list[AnomalyFlag] = []
    cash_in = transactions.loc[
        transactions["transaction_type"] == "cash_in"
    ].sort_values("occurred_at")

    for provider_code, group in cash_in.groupby("provider_code"):
        group = group.reset_index(drop=True)
        used_indices: set[int] = set()

        for anchor_position in range(len(group)):
            if anchor_position in used_indices:
                continue
            anchor = group.iloc[anchor_position]
            window_end = anchor["occurred_at"] + pd.Timedelta(
                minutes=REPEAT_WINDOW_MINUTES
            )
            in_window = group.loc[
                (group["occurred_at"] >= anchor["occurred_at"])
                & (group["occurred_at"] <= window_end)
            ]
            tolerance = anchor["amount"] * REPEAT_AMOUNT_TOLERANCE
            similar = in_window.loc[
                (in_window["amount"] - anchor["amount"]).abs() <= tolerance
            ]
            if len(similar) < REPEAT_MIN_COUNT:
                continue

            used_indices.update(similar.index.tolist())
            repeat_count = int(len(similar))
            span_minutes = (
                similar["occurred_at"].max() - similar["occurred_at"].min()
            ).total_seconds() / 60.0

            # More repeats in a tighter window -> higher confidence.
            confidence = min(
                0.95,
                0.55
                + 0.06 * (repeat_count - REPEAT_MIN_COUNT)
                + (0.15 if span_minutes <= 30 else 0.0),
            )
            severity = "high" if repeat_count >= 5 else "medium"

            flags.append(
                AnomalyFlag(
                    flag_id=(
                        f"{scenario_id}-REPEAT-{provider_code}-"
                        f"{anchor['external_id']}"
                    ),
                    category="repeated_amounts",
                    severity=severity,
                    provider_code=str(provider_code),
                    title=(
                        f"{repeat_count} similar cash-in amounts on "
                        f"{provider_code} within "
                        f"{max(int(span_minutes), 1)} minutes"
                    ),
                    reason=(
                        f"{repeat_count} cash-in transactions of roughly "
                        f"{anchor['amount']:,.0f} occurred within "
                        f"{REPEAT_WINDOW_MINUTES} minutes. Repeated "
                        "near-identical amounts are unusual against the "
                        "normal mixed pattern."
                    ),
                    confidence=confidence,
                    uncertainty=(
                        "A local event (e.g. salary day or a market fair) "
                        "can also produce repeated amounts. Human review "
                        "is required before any action."
                    ),
                    recommended_next_step=(
                        "Review the flagged transactions with the agent, "
                        "confirm the provider feed is fresh, and record "
                        "the outcome in case management."
                    ),
                    evidence=similar.reset_index(drop=True),
                    metrics={
                        "repeated_amount": float(anchor["amount"]),
                        "repeat_count": repeat_count,
                        "window_minutes": REPEAT_WINDOW_MINUTES,
                        "span_minutes": round(span_minutes, 1),
                    },
                )
            )

    return flags


def _detect_velocity_spike(
    transactions: pd.DataFrame,
    scenario_id: str,
) -> list[AnomalyFlag]:
    flags: list[AnomalyFlag] = []
    if transactions.empty:
        return flags

    end_time = transactions["occurred_at"].max()
    recent_start = end_time - pd.Timedelta(
        minutes=VELOCITY_RECENT_WINDOW_MINUTES
    )
    baseline = transactions.loc[transactions["occurred_at"] < recent_start]
    recent = transactions.loc[transactions["occurred_at"] >= recent_start]

    if baseline.empty or recent.empty:
        return flags

    baseline_hours = max(
        (recent_start - transactions["occurred_at"].min()).total_seconds()
        / 3600.0,
        0.25,
    )
    baseline_rate = len(baseline) / baseline_hours
    recent_rate = len(recent) / (VELOCITY_RECENT_WINDOW_MINUTES / 60.0)

    if baseline_rate <= 0:
        return flags

    ratio = recent_rate / baseline_rate
    if ratio < VELOCITY_RATIO_THRESHOLD:
        return flags

    top_provider = recent["provider_code"].mode().iloc[0]
    confidence = min(0.9, 0.5 + 0.1 * (ratio - VELOCITY_RATIO_THRESHOLD))

    flags.append(
        AnomalyFlag(
            flag_id=f"{scenario_id}-VELOCITY-{top_provider}",
            category="velocity_spike",
            severity="medium" if ratio < 3 else "high",
            provider_code=str(top_provider),
            title=(
                f"Transaction velocity {ratio:.1f}x above baseline in the "
                "last hour"
            ),
            reason=(
                f"About {recent_rate:.1f} transactions/hour occurred in the "
                f"last {VELOCITY_RECENT_WINDOW_MINUTES} minutes versus a "
                f"baseline of {baseline_rate:.1f}/hour, concentrated on "
                f"{top_provider}."
            ),
            confidence=confidence,
            uncertainty=(
                "Short bursts can reflect legitimate demand spikes. The "
                "ratio is sensitive to the small demo sample size."
            ),
            recommended_next_step=(
                "Compare against the agent's usual peak hours and check "
                "whether float levels can absorb the increased demand."
            ),
            evidence=recent.reset_index(drop=True),
            metrics={
                "velocity_ratio": round(ratio, 2),
                "recent_rate_per_hour": round(recent_rate, 2),
                "baseline_rate_per_hour": round(baseline_rate, 2),
            },
        )
    )

    return flags


def detect_anomalies(
    repository: DemoDataRepository,
    scenario_id: str,
    agent_code: str,
    provider_code: str | None = None,
) -> list[AnomalyFlag]:
    """Run all detection rules for one agent within one scenario."""

    transactions = repository.transactions_for(
        scenario_id,
        agent_code,
        provider_code,
    )
    if transactions.empty:
        return []

    flags = _detect_repeated_amounts(transactions, scenario_id)
    flags.extend(_detect_velocity_spike(transactions, scenario_id))

    severity_order = {"high": 0, "medium": 1, "low": 2}
    flags.sort(key=lambda flag: (severity_order[flag.severity], -flag.confidence))
    return flags
