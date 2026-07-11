"""Definitions for deterministic synthetic demonstration scenarios."""

from dataclasses import dataclass
from datetime import UTC, datetime


PROVIDER_CODES = (
    "BKASH_SIM",
    "NAGAD_SIM",
    "ROCKET_SIM",
)

AGENT_CODE = "AGENT-SYL-001"

BASE_TIME = datetime(
    2026,
    7,
    11,
    8,
    0,
    tzinfo=UTC,
)


@dataclass(frozen=True)
class ScenarioDefinition:
    """Describe one synthetic demonstration scenario."""

    scenario_id: str
    name: str
    description: str
    anomaly_expected: bool
    anomaly_category: str | None
    expected_shortage_resource: str | None
    injection_start_time: datetime | None
    expected_shortage_time: datetime | None


SCENARIOS = (
    ScenarioDefinition(
        scenario_id="NORMAL-001",
        name="Normal operation",
        description=(
            "Stable shared cash and healthy balances across "
            "all synthetic providers."
        ),
        anomaly_expected=False,
        anomaly_category=None,
        expected_shortage_resource=None,
        injection_start_time=None,
        expected_shortage_time=None,
    ),
    ScenarioDefinition(
        scenario_id="SHORTAGE-001",
        name="Hidden provider shortage",
        description=(
            "BKASH_SIM is under pressure while other provider "
            "balances remain healthy."
        ),
        anomaly_expected=False,
        anomaly_category=None,
        expected_shortage_resource="BKASH_SIM",
        injection_start_time=datetime(
            2026,
            7,
            11,
            12,
            0,
            tzinfo=UTC,
        ),
        expected_shortage_time=datetime(
            2026,
            7,
            11,
            16,
            30,
            tzinfo=UTC,
        ),
    ),
    ScenarioDefinition(
        scenario_id="REPEATED-001",
        name="Repeated amounts and increased velocity",
        description=(
            "Several similar BKASH_SIM cash-in transactions "
            "occur in a short time window."
        ),
        anomaly_expected=True,
        anomaly_category="repeated_amounts",
        expected_shortage_resource="BKASH_SIM",
        injection_start_time=datetime(
            2026,
            7,
            11,
            13,
            0,
            tzinfo=UTC,
        ),
        expected_shortage_time=datetime(
            2026,
            7,
            11,
            17,
            0,
            tzinfo=UTC,
        ),
    ),
    ScenarioDefinition(
        scenario_id="STALE-001",
        name="Delayed provider feed",
        description=(
            "ROCKET_SIM position data becomes delayed, "
            "reducing forecast confidence."
        ),
        anomaly_expected=False,
        anomaly_category=None,
        expected_shortage_resource=None,
        injection_start_time=datetime(
            2026,
            7,
            11,
            14,
            0,
            tzinfo=UTC,
        ),
        expected_shortage_time=None,
    ),
)