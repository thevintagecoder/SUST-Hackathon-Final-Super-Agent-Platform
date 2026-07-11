"""Mock data provider backed by local JSON files."""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from pathlib import Path

from frontend.data.contracts import (
    load_json_file,
    validate_alerts,
    validate_case,
    validate_liquidity,
    validate_overview,
)


class MockDataProvider:
    """Serve dashboard data from frontend/mock_data JSON files."""

    def __init__(self, mock_data_dir: Path) -> None:
        self._mock_data_dir = mock_data_dir
        self._overview: dict | None = None
        self._liquidity: dict | None = None
        self._alerts: list[dict] | None = None
        self._cases: dict[int, dict] = {}

    def _now_iso(self) -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00",
            "Z",
        )

    def _load_overview(self) -> dict:
        if self._overview is None:
            payload = load_json_file(self._mock_data_dir / "overview.json")
            self._overview = validate_overview(payload)
        return copy.deepcopy(self._overview)

    def _load_liquidity(self) -> dict:
        if self._liquidity is None:
            payload = load_json_file(self._mock_data_dir / "liquidity.json")
            self._liquidity = validate_liquidity(payload)
        return copy.deepcopy(self._liquidity)

    def _load_alerts(self) -> list[dict]:
        if self._alerts is None:
            payload = load_json_file(self._mock_data_dir / "alerts.json")
            self._alerts = validate_alerts(payload)
        return copy.deepcopy(self._alerts)

    def _load_case(self, case_id: int) -> dict:
        if case_id not in self._cases:
            payload = load_json_file(self._mock_data_dir / "case.json")
            validated = validate_case(payload)
            if validated["id"] != case_id:
                raise ValueError(f"Case {case_id} was not found in mock data.")
            self._cases[case_id] = validated
        return copy.deepcopy(self._cases[case_id])

    def get_overview(self) -> dict:
        return self._load_overview()

    def get_liquidity(self, agent_code: str) -> dict:
        liquidity = self._load_liquidity()
        if liquidity["agent_code"] != agent_code:
            raise ValueError(
                f"Liquidity data is unavailable for agent '{agent_code}'."
            )
        return liquidity

    def list_alerts(self) -> list[dict]:
        return self._load_alerts()

    def get_case(self, case_id: int) -> dict:
        return self._load_case(case_id)

    def acknowledge_alert(self, alert_id: int, actor: str) -> dict:
        alerts = self._load_alerts()
        alert = next((item for item in alerts if item["id"] == alert_id), None)
        if alert is None:
            raise ValueError(f"Alert {alert_id} was not found.")

        if alert["status"] == "acknowledged":
            return {
                "success": True,
                "message": f"Alert {alert_id} is already acknowledged.",
            }

        alert["status"] = "acknowledged"
        self._alerts = alerts

        overview = self._load_overview()
        if overview["unacknowledged_alerts"] > 0:
            overview["unacknowledged_alerts"] -= 1
        self._overview = overview

        case = self._load_case(501)
        if case["alert_id"] == alert_id:
            case["timeline"].append(
                {
                    "event": "acknowledged",
                    "actor": actor,
                    "at": self._now_iso(),
                    "note": f"Alert {alert_id} acknowledged",
                }
            )
            self._cases[case["id"]] = case

        return {
            "success": True,
            "message": f"Alert {alert_id} acknowledged by {actor}.",
        }

    def add_case_note(self, case_id: int, actor: str, note: str) -> dict:
        case = self._load_case(case_id)
        cleaned_note = note.strip()
        if not cleaned_note:
            raise ValueError("Case note must not be empty.")

        case["timeline"].append(
            {
                "event": "note",
                "actor": actor,
                "at": self._now_iso(),
                "note": cleaned_note,
            }
        )
        self._cases[case_id] = case
        return {
            "success": True,
            "message": "Case note added.",
        }

    def assign_case(self, case_id: int, owner: str) -> dict:
        cleaned_owner = owner.strip()
        if not cleaned_owner:
            raise ValueError("Case owner must not be empty.")

        case = self._load_case(case_id)
        case["owner"] = cleaned_owner
        case["timeline"].append(
            {
                "event": "assigned",
                "actor": "system",
                "at": self._now_iso(),
                "note": f"Case assigned to {cleaned_owner}",
            }
        )
        self._cases[case_id] = case
        return {
            "success": True,
            "message": f"Case {case_id} assigned to {cleaned_owner}.",
        }

    def update_case_status(self, case_id: int, status: str) -> dict:
        allowed_statuses = {
            "investigating",
            "escalated",
            "resolved",
        }
        cleaned_status = status.strip().lower()
        if cleaned_status not in allowed_statuses:
            raise ValueError(
                f"Unsupported case status '{status}'. "
                f"Expected one of {sorted(allowed_statuses)}."
            )

        case = self._load_case(case_id)
        case["status"] = cleaned_status
        case["timeline"].append(
            {
                "event": "status",
                "actor": "system",
                "at": self._now_iso(),
                "note": f"Status updated to {cleaned_status}",
            }
        )
        self._cases[case_id] = case
        return {
            "success": True,
            "message": f"Case {case_id} status updated to {cleaned_status}.",
        }
