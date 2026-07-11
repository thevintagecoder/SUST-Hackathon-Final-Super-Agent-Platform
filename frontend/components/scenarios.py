"""Demo scenario metadata — no Streamlit or heavy deps."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioInfo:
    """Describe one demo scenario for operator display."""

    scenario_id: str
    label: str
    what_it_tests: str
    interesting_result: str
    css_class: str


SCENARIO_REGISTRY: dict[str, ScenarioInfo] = {
    "NORMAL-001": ScenarioInfo(
        scenario_id="NORMAL-001",
        label="Normal operation",
        what_it_tests=(
            "All four agents have healthy cash and provider balances. "
            "Zindabazar has ৳50,000 shared cash; bKash/Nagad/Rocket floats "
            "all ৳58–62k and live."
        ),
        interesting_result="Should show: fully serviceable, no alerts needed.",
        css_class="ok",
    ),
    "SHORTAGE-001": ScenarioInfo(
        scenario_id="SHORTAGE-001",
        label="Hidden bKash shortage",
        what_it_tests=(
            "Zindabazar bKash float has only ৳18,000. "
            "Try checking a ৳50,000 bKash cash-in request."
        ),
        interesting_result="Should show: NOT SERVICEABLE — short by ৳32,000.",
        css_class="danger",
    ),
    "REPEATED-001": ScenarioInfo(
        scenario_id="REPEATED-001",
        label="Repeated bKash transactions",
        what_it_tests=(
            "Five similar bKash cash-in amounts hit in one hour, then float "
            "drops below safety. Run the 'Unusual activity' check."
        ),
        interesting_result="Should show: ANOMALY DETECTED — repeated_amounts pattern.",
        css_class="danger",
    ),
    "STALE-001": ScenarioInfo(
        scenario_id="STALE-001",
        label="Rocket feed delayed",
        what_it_tests=(
            "Rocket's balance data is 2 hours old (delayed). "
            "Check stale-data alert or open the Agent desk to see it."
        ),
        interesting_result="Should show: Rocket feed marked as 'delayed'.",
        css_class="warn",
    ),
    "NETWORK-001": ScenarioInfo(
        scenario_id="NETWORK-001",
        label="Multi-agent coordination",
        what_it_tests=(
            "Zindabazar has only ৳20,000 Nagad float — cannot serve "
            "a ৳80,000 cash-in. Nearby Ambarkhana has ৳120,000 Nagad."
        ),
        interesting_result=(
            "Should show: local NOT SERVICEABLE, "
            "Ambarkhana (1.2 km) is the recommended helper."
        ),
        css_class="warn",
    ),
    "FORECAST-001": ScenarioInfo(
        scenario_id="FORECAST-001",
        label="Nagad float runway",
        what_it_tests=(
            "Zindabazar started with ৳100,000 Nagad float. Six transactions "
            "over the last 6 hours burned ৳45,000 net (৳7,500/hr rate). "
            "Safety threshold is ৳40,000."
        ),
        interesting_result=(
            "Should show: HIGH risk — only ~8 hours before Nagad float "
            "hits the safety threshold."
        ),
        css_class="danger",
    ),
}
