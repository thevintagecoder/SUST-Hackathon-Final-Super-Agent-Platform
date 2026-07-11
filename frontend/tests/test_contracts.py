"""Contract validation tests for frontend mock data."""

from __future__ import annotations

from pathlib import Path

import pytest

from frontend.data.contracts import (
    APPROVED_PROVIDER_CODES,
    load_json_file,
    validate_alerts,
    validate_case,
    validate_liquidity,
    validate_overview,
)
from frontend.data.mock_provider import MockDataProvider

MOCK_DATA_DIR = Path(__file__).resolve().parents[1] / "mock_data"


def test_overview_contract() -> None:
    overview = validate_overview(load_json_file(MOCK_DATA_DIR / "overview.json"))

    assert overview["agent"]["code"] == "AGENT-SYL-001"
    assert overview["shared_cash"]["amount"] == 42000.0
    assert len(overview["providers"]) == 3
    assert {provider["code"] for provider in overview["providers"]} == set(
        APPROVED_PROVIDER_CODES
    )


def test_liquidity_contract() -> None:
    liquidity = validate_liquidity(
        load_json_file(MOCK_DATA_DIR / "liquidity.json")
    )

    bkash = next(
        position
        for position in liquidity["positions"]
        if position["resource"] == "BKASH_SIM"
    )
    assert bkash["estimated_runway_hours"] == pytest.approx(3.27)
    assert bkash["warning_threshold_hours"] == 6.0
    assert bkash["confidence"] == pytest.approx(0.82)


def test_alerts_contract() -> None:
    alerts = validate_alerts(load_json_file(MOCK_DATA_DIR / "alerts.json"))

    assert len(alerts) >= 1
    assert alerts[0]["id"] == 101
    assert "confirmed fraud" not in alerts[0]["title"].lower()


def test_case_contract() -> None:
    case = validate_case(load_json_file(MOCK_DATA_DIR / "case.json"))

    assert case["id"] == 501
    assert case["alert_id"] == 101
    assert len(case["timeline"]) >= 3


def test_mock_provider_returns_expected_shapes() -> None:
    provider = MockDataProvider(mock_data_dir=MOCK_DATA_DIR)

    overview = provider.get_overview()
    liquidity = provider.get_liquidity("AGENT-SYL-001")
    alerts = provider.list_alerts()
    case = provider.get_case(501)

    validate_overview(overview)
    validate_liquidity(liquidity)
    validate_alerts(alerts)
    validate_case(case)


def test_mock_provider_mutations() -> None:
    provider = MockDataProvider(mock_data_dir=MOCK_DATA_DIR)

    acknowledge_result = provider.acknowledge_alert(101, "ops-user-02")
    note_result = provider.add_case_note(
        501,
        "ops-user-02",
        "Checked local event schedule",
    )
    status_result = provider.update_case_status(501, "escalated")

    assert acknowledge_result["success"] is True
    assert note_result["success"] is True
    assert status_result["success"] is True

    alerts = provider.list_alerts()
    alert = next(item for item in alerts if item["id"] == 101)
    assert alert["status"] == "acknowledged"

    case = provider.get_case(501)
    assert case["status"] == "escalated"
    assert case["timeline"][-1]["event"] == "status"
