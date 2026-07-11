"""Typed contracts and validators for frontend data payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

APPROVED_PROVIDER_CODES = frozenset(
    {"BKASH_SIM", "NAGAD_SIM", "ROCKET_SIM"}
)

FORBIDDEN_PHRASES = (
    "confirmed fraud",
    "fraudulent agent",
)


class AgentInfo(TypedDict):
    code: str
    name: str
    area: str


class SharedCash(TypedDict):
    amount: float
    freshness: str
    as_of: str


class ProviderPosition(TypedDict):
    code: str
    balance: float
    status: str
    freshness: str


class OverviewData(TypedDict):
    generated_at: str
    agent: AgentInfo
    shared_cash: SharedCash
    providers: list[ProviderPosition]
    open_alerts: int
    unacknowledged_alerts: int


class LiquidityEvidence(TypedDict):
    window_hours: int
    sample_size: int
    volatility: float


class LiquidityPosition(TypedDict):
    resource: str
    current_balance: float
    recent_net_outflow_per_hour: float
    estimated_runway_hours: float
    warning_threshold_hours: float
    confidence: float
    freshness: str
    evidence: LiquidityEvidence


class LiquidityData(TypedDict):
    agent_code: str
    positions: list[LiquidityPosition]


class AlertEvidence(TypedDict, total=False):
    repeated_amount: float
    repeat_count: int
    velocity_ratio: float
    runway_hours: float


class Alert(TypedDict):
    id: int
    type: str
    severity: str
    status: str
    title: str
    reason: str
    confidence: float
    uncertainty: str
    evidence: AlertEvidence
    recommended_next_step: str
    owner: str
    created_at: str


class TimelineEvent(TypedDict):
    event: str
    actor: str
    at: str
    note: str


class CaseData(TypedDict):
    id: int
    alert_id: int
    status: str
    owner: str
    timeline: list[TimelineEvent]


class ActionResponse(TypedDict):
    success: bool
    message: str


def _assert_confidence(value: float, context: str) -> None:
    if not 0 <= value <= 1:
        raise ValueError(
            f"{context}: confidence must be between 0 and 1, got {value}"
        )


def _assert_no_forbidden_language(payload: Any, path: str = "root") -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            _assert_no_forbidden_language(value, f"{path}.{key}")
        return

    if isinstance(payload, list):
        for index, item in enumerate(payload):
            _assert_no_forbidden_language(item, f"{path}[{index}]")
        return

    if isinstance(payload, str):
        lowered = payload.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                raise ValueError(
                    f"{path}: forbidden phrase '{phrase}' found in text"
                )


def validate_overview(data: dict[str, Any]) -> OverviewData:
    """Validate overview payload shape and responsible-language rules."""

    required = {
        "generated_at",
        "agent",
        "shared_cash",
        "providers",
        "open_alerts",
        "unacknowledged_alerts",
    }
    missing = required - data.keys()
    if missing:
        raise ValueError(f"overview missing keys: {sorted(missing)}")

    providers = data["providers"]
    if len(providers) != 3:
        raise ValueError("overview must include exactly three providers")

    codes = {provider["code"] for provider in providers}
    if codes != APPROVED_PROVIDER_CODES:
        raise ValueError(
            f"overview providers must be {sorted(APPROVED_PROVIDER_CODES)}"
        )

    _assert_no_forbidden_language(data)
    return data  # type: ignore[return-value]


def validate_liquidity(data: dict[str, Any]) -> LiquidityData:
    """Validate liquidity payload shape."""

    required = {"agent_code", "positions"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"liquidity missing keys: {sorted(missing)}")

    for index, position in enumerate(data["positions"]):
        if position["resource"] not in APPROVED_PROVIDER_CODES:
            raise ValueError(
                f"positions[{index}] has invalid resource "
                f"{position['resource']}"
            )
        _assert_confidence(
            position["confidence"],
            f"positions[{index}]",
        )

    _assert_no_forbidden_language(data)
    return data  # type: ignore[return-value]


def validate_alerts(data: list[dict[str, Any]]) -> list[Alert]:
    """Validate alerts list payload shape."""

    if not isinstance(data, list):
        raise ValueError("alerts payload must be a list")

    for index, alert in enumerate(data):
        _assert_confidence(alert["confidence"], f"alerts[{index}]")

    _assert_no_forbidden_language(data)
    return data  # type: ignore[return-value]


def validate_case(data: dict[str, Any]) -> CaseData:
    """Validate case payload shape."""

    required = {"id", "alert_id", "status", "owner", "timeline"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"case missing keys: {sorted(missing)}")

    if not data["timeline"]:
        raise ValueError("case timeline must not be empty")

    _assert_no_forbidden_language(data)
    return data  # type: ignore[return-value]


def load_json_file(path: Path) -> Any:
    """Load and parse one JSON file."""

    with path.open(encoding="utf-8") as handle:
        return json.load(handle)
