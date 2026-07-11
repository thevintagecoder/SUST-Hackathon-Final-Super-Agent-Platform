"""HTTP data provider for integrated FastAPI mode."""

from __future__ import annotations

import requests


class ApiDataError(Exception):
    """Raised when the FastAPI backend is unavailable or returns an error."""


class ApiDataProvider:
    """Serve dashboard data from FastAPI over HTTP."""

    def __init__(self, base_url: str, timeout_seconds: int = 3) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
    ) -> dict | list:
        url = f"{self._base_url}{path}"
        try:
            response = requests.request(
                method=method,
                url=url,
                json=json_body,
                timeout=self._timeout_seconds,
            )
        except requests.Timeout as exc:
            raise ApiDataError(
                f"API request timed out after {self._timeout_seconds} seconds."
            ) from exc
        except requests.ConnectionError as exc:
            raise ApiDataError(
                f"Cannot reach API at {self._base_url}. Is FastAPI running?"
            ) from exc

        if not response.ok:
            detail = response.text.strip() or response.reason
            raise ApiDataError(
                f"API request failed ({response.status_code}): {detail}"
            )

        if not response.content:
            return {}

        payload = response.json()
        if isinstance(payload, (dict, list)):
            return payload
        raise ApiDataError("API response was not valid JSON.")

    def get_overview(self) -> dict:
        payload = self._request("GET", "/dashboard/overview")
        if not isinstance(payload, dict):
            raise ApiDataError("Overview endpoint did not return an object.")
        return payload

    def get_liquidity(self, agent_code: str) -> dict:
        payload = self._request(
            "GET",
            f"/dashboard/liquidity/{agent_code}",
        )
        if not isinstance(payload, dict):
            raise ApiDataError("Liquidity endpoint did not return an object.")
        return payload

    def list_alerts(self) -> list[dict]:
        payload = self._request("GET", "/dashboard/alerts")
        if not isinstance(payload, list):
            raise ApiDataError("Alerts endpoint did not return a list.")
        return payload

    def get_case(self, case_id: int) -> dict:
        payload = self._request("GET", f"/dashboard/cases/{case_id}")
        if not isinstance(payload, dict):
            raise ApiDataError("Case endpoint did not return an object.")
        return payload

    def acknowledge_alert(self, alert_id: int, actor: str) -> dict:
        payload = self._request(
            "POST",
            f"/dashboard/alerts/{alert_id}/acknowledge",
            json_body={"actor": actor},
        )
        if not isinstance(payload, dict):
            raise ApiDataError(
                "Acknowledge endpoint did not return an object."
            )
        return payload

    def add_case_note(self, case_id: int, actor: str, note: str) -> dict:
        payload = self._request(
            "POST",
            f"/dashboard/cases/{case_id}/notes",
            json_body={"actor": actor, "note": note},
        )
        if not isinstance(payload, dict):
            raise ApiDataError("Add-note endpoint did not return an object.")
        return payload

    def assign_case(self, case_id: int, owner: str) -> dict:
        payload = self._request(
            "POST",
            f"/dashboard/cases/{case_id}/assign",
            json_body={"owner": owner},
        )
        if not isinstance(payload, dict):
            raise ApiDataError("Assign endpoint did not return an object.")
        return payload

    def update_case_status(self, case_id: int, status: str) -> dict:
        payload = self._request(
            "PATCH",
            f"/dashboard/cases/{case_id}/status",
            json_body={"status": status},
        )
        if not isinstance(payload, dict):
            raise ApiDataError(
                "Update-status endpoint did not return an object."
            )
        return payload
