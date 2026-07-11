"""Definitions for deterministic synthetic demonstration scenarios."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal


PROVIDER_CODES = (
    "BKASH_SIM",
    "NAGAD_SIM",
    "ROCKET_SIM",
)

BASE_TIME = datetime(
    2026,
    7,
    11,
    8,
    0,
    tzinfo=UTC,
)

NETWORK_SCENARIO_ID = "NETWORK-001"
FORECAST_SCENARIO_ID = "FORECAST-001"

FORECAST_AS_OF = BASE_TIME + timedelta(
    hours=6,
)

FORECAST_ACTUAL_BREACH_TIME = (
    FORECAST_AS_OF
    + timedelta(
        hours=8,
        minutes=30,
    )
)


@dataclass(frozen=True)
class AgentDefinition:
    """Describe one clearly synthetic demonstration Agent."""

    agent_code: str
    name: str
    area: str
    latitude: Decimal
    longitude: Decimal
    is_active: bool = True


AGENTS = (
    AgentDefinition(
        agent_code="AGENT-SYL-001",
        name="Synthetic Zindabazar Agent",
        area="Sylhet",
        latitude=Decimal("24.894900"),
        longitude=Decimal("91.868700"),
    ),
    AgentDefinition(
        agent_code="AGENT-SYL-002",
        name="Synthetic Ambarkhana Agent",
        area="Sylhet",
        latitude=Decimal("24.900100"),
        longitude=Decimal("91.875200"),
    ),
    AgentDefinition(
        agent_code="AGENT-SYL-003",
        name="Synthetic Bondor Agent",
        area="Sylhet",
        latitude=Decimal("24.887200"),
        longitude=Decimal("91.860400"),
    ),
    AgentDefinition(
        agent_code="AGENT-SYL-004",
        name="Synthetic Shibgonj Agent",
        area="Sylhet",
        latitude=Decimal("24.908000"),
        longitude=Decimal("91.852000"),
    ),
)

# Kept for compatibility with existing single-Agent scenarios.
AGENT_CODE = AGENTS[0].agent_code


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
    ScenarioDefinition(
        scenario_id=NETWORK_SCENARIO_ID,
        name="Multi-Agent liquidity coordination",
        description=(
            "AGENT-SYL-001 cannot serve a large Nagad cash-in. "
            "Nearby Agents have different provider-float, physical-"
            "cash, distance, and data-freshness characteristics."
        ),
        anomaly_expected=False,
        anomaly_category=None,
        expected_shortage_resource="NAGAD_SIM",
        injection_start_time=datetime(
            2026,
            7,
            11,
            15,
            0,
            tzinfo=UTC,
        ),
        expected_shortage_time=None,
    ),

    ScenarioDefinition(
        scenario_id=FORECAST_SCENARIO_ID,
        name="Deterministic liquidity runway forecast",
        description=(
            "A fixed Nagad electronic-float consumption pattern "
            "is used to evaluate forecast error and shortage-"
            "warning lead time."
        ),
        anomaly_expected=False,
        anomaly_category=None,
        expected_shortage_resource="NAGAD_SIM",
        injection_start_time=FORECAST_AS_OF,
        expected_shortage_time=(
            FORECAST_ACTUAL_BREACH_TIME
        ),
    ),
)