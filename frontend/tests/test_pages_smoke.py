"""Smoke tests: every dashboard page renders without an exception.

Uses Streamlit's AppTest harness, so these tests need streamlit
installed (they run locally; CI runs the logic tests).
"""

from __future__ import annotations

from pathlib import Path

import pytest

streamlit_testing = pytest.importorskip("streamlit.testing.v1")

PAGES_DIR = Path(__file__).resolve().parents[1] / "pages"

PAGE_FILES = [
    "Home.py",
    "1_Liquidity_Forecast.py",
    "2_Anomaly_Alerts.py",
    "3_Agent_Risk_Explorer.py",
    "4_Admin_Case_Management.py",
]


@pytest.mark.parametrize("page_file", PAGE_FILES)
def test_page_renders_without_exception(page_file: str) -> None:
    app_test = streamlit_testing.AppTest.from_file(
        str(PAGES_DIR / page_file),
        default_timeout=30,
    )
    app_test.run()

    assert not app_test.exception, (
        f"{page_file} raised: "
        f"{[item.value for item in app_test.exception]}"
    )


@pytest.mark.parametrize(
    "scenario_id",
    ["NORMAL-001", "SHORTAGE-001", "REPEATED-001", "STALE-001"],
)
def test_forecast_page_renders_every_scenario(scenario_id: str) -> None:
    app_test = streamlit_testing.AppTest.from_file(
        str(PAGES_DIR / "1_Liquidity_Forecast.py"),
        default_timeout=30,
    )
    app_test.session_state["filter_scenario"] = scenario_id
    app_test.run()

    assert not app_test.exception


def test_risk_explorer_bangla_toggle() -> None:
    app_test = streamlit_testing.AppTest.from_file(
        str(PAGES_DIR / "3_Agent_Risk_Explorer.py"),
        default_timeout=30,
    )
    app_test.session_state["filter_scenario"] = "REPEATED-001"
    app_test.run()
    assert not app_test.exception

    app_test.radio(key="risk_language").set_value("বাংলা").run()
    assert not app_test.exception
