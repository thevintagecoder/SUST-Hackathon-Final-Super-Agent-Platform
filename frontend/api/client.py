"""HTTP client for communication with the FastAPI backend."""

from __future__ import annotations

from typing import Any

import httpx


DEFAULT_TIMEOUT_SECONDS = 30.0


class BackendAPIError(RuntimeError):
    """Raised when the frontend cannot use the backend API."""


def _clean_params(
    params: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Drop None values so query strings stay valid."""

    if params is None:
        return None

    cleaned = {
        key: value
        for key, value in params.items()
        if value is not None and value != ""
    }

    return cleaned or None


class BackendClient:
    """Provide centralized access to FastAPI endpoints."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Create a configured backend HTTP client."""

        normalized_base_url = base_url.strip().rstrip("/")

        if not normalized_base_url:
            raise ValueError(
                "The backend base URL cannot be empty."
            )

        self.base_url = normalized_base_url

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout_seconds,
            transport=transport,
            headers={
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""

        self._client.close()

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a request and return a JSON object."""

        try:
            response = self._client.request(
                method=method,
                url=path,
                params=_clean_params(params),
                json=json,
            )

            response.raise_for_status()

        except httpx.TimeoutException as error:
            raise BackendAPIError(
                "The backend request timed out. "
                "Confirm PostgreSQL is running and the "
                "API is reachable."
            ) from error

        except httpx.ConnectError as error:
            raise BackendAPIError(
                "The frontend could not connect to FastAPI. "
                "Confirm that the backend is running at "
                f"{self.base_url}."
            ) from error

        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code

            try:
                error_body = error.response.json()
            except ValueError:
                error_body = error.response.text

            raise BackendAPIError(
                "The backend returned HTTP "
                f"{status_code}: {error_body}"
            ) from error

        except httpx.RequestError as error:
            raise BackendAPIError(
                f"Backend request failed: {error}"
            ) from error

        try:
            response_data = response.json()
        except ValueError as error:
            raise BackendAPIError(
                "The backend returned invalid JSON."
            ) from error

        if not isinstance(response_data, dict):
            raise BackendAPIError(
                "The backend response must be a JSON object."
            )

        return response_data

    # --- System ---

    def health(self) -> dict[str, Any]:
        """Return the backend process health response."""

        return self._request_json(
            method="GET",
            path="/health",
        )

    def health_database(self) -> dict[str, Any]:
        """Return the backend database health response."""

        return self._request_json(
            method="GET",
            path="/health/database",
        )

    # --- Agents ---

    def create_agent(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Create one Agent record."""

        return self._request_json(
            method="POST",
            path="/agents",
            json=payload,
        )

    # --- Liquidity / Network ---

    def check_serviceability(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Check whether a transaction is serviceable."""

        return self._request_json(
            method="POST",
            path="/liquidity/check-serviceability",
            json=payload,
        )

    def find_network_support(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Find nearby Agents that can provide support."""

        return self._request_json(
            method="POST",
            path="/network/find-support",
            json=payload,
        )

    # --- Support requests ---

    def create_support_request(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Create one support-request workflow."""

        return self._request_json(
            method="POST",
            path="/support-requests",
            json=payload,
        )

    def list_support_requests(
        self,
        *,
        status: str | None = None,
    ) -> dict[str, Any]:
        """List support requests, optionally by status."""

        return self._request_json(
            method="GET",
            path="/support-requests",
            params={"status": status},
        )

    def get_support_request(
        self,
        support_request_id: int,
    ) -> dict[str, Any]:
        """Return one support request by id."""

        return self._request_json(
            method="GET",
            path=f"/support-requests/{support_request_id}",
        )

    def accept_support_request(
        self,
        support_request_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Accept one support request."""

        return self._request_json(
            method="POST",
            path=(
                f"/support-requests/{support_request_id}/accept"
            ),
            json=payload,
        )

    def reject_support_request(
        self,
        support_request_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Reject one support request."""

        return self._request_json(
            method="POST",
            path=(
                f"/support-requests/{support_request_id}/reject"
            ),
            json=payload,
        )

    def escalate_support_request(
        self,
        support_request_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Escalate one support request."""

        return self._request_json(
            method="POST",
            path=(
                f"/support-requests/"
                f"{support_request_id}/escalate"
            ),
            json=payload,
        )

    def resolve_support_request(
        self,
        support_request_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve one support request."""

        return self._request_json(
            method="POST",
            path=(
                f"/support-requests/"
                f"{support_request_id}/resolve"
            ),
            json=payload,
        )

    def add_support_request_note(
        self,
        support_request_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Add a note to one support request."""

        return self._request_json(
            method="POST",
            path=(
                f"/support-requests/{support_request_id}/notes"
            ),
            json=payload,
        )

    # --- Forecasts / Anomalies ---

    def forecast_liquidity_runway(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Estimate liquidity runway for one Agent."""

        return self._request_json(
            method="POST",
            path="/forecasts/liquidity-runway",
            json=payload,
        )

    def detect_anomaly(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Run anomaly detection for one Agent."""

        return self._request_json(
            method="POST",
            path="/anomalies/detect",
            json=payload,
        )

    # --- Alerts ---

    def generate_alert(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate and optionally persist one alert."""

        return self._request_json(
            method="POST",
            path="/alerts/generate",
            json=payload,
        )

    def list_alerts(
        self,
        *,
        status: str | None = None,
        alert_type: str | None = None,
        agent_code: str | None = None,
        provider_code: str | None = None,
        scenario_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List alerts with optional filters."""

        return self._request_json(
            method="GET",
            path="/alerts",
            params={
                "status": status,
                "alert_type": alert_type,
                "agent_code": agent_code,
                "provider_code": provider_code,
                "scenario_id": scenario_id,
                "limit": limit,
                "offset": offset,
            },
        )

    def get_alert(
        self,
        alert_id: int,
    ) -> dict[str, Any]:
        """Return one alert detail record."""

        return self._request_json(
            method="GET",
            path=f"/alerts/{alert_id}",
        )

    def acknowledge_alert(
        self,
        alert_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Acknowledge one alert."""

        return self._request_json(
            method="POST",
            path=f"/alerts/{alert_id}/acknowledge",
            json=payload,
        )

    def assign_alert(
        self,
        alert_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Assign one alert to a reviewer."""

        return self._request_json(
            method="POST",
            path=f"/alerts/{alert_id}/assign",
            json=payload,
        )

    def add_alert_note(
        self,
        alert_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Add a note to one alert."""

        return self._request_json(
            method="POST",
            path=f"/alerts/{alert_id}/notes",
            json=payload,
        )

    def escalate_alert(
        self,
        alert_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Escalate one alert."""

        return self._request_json(
            method="POST",
            path=f"/alerts/{alert_id}/escalate",
            json=payload,
        )

    def resolve_alert(
        self,
        alert_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve one alert."""

        return self._request_json(
            method="POST",
            path=f"/alerts/{alert_id}/resolve",
            json=payload,
        )

    # --- Dashboards ---

    def agent_dashboard(
        self,
        agent_code: str,
        *,
        scenario_id: str | None = None,
        recent_alert_limit: int = 5,
    ) -> dict[str, Any]:
        """Return the Agent stakeholder dashboard."""

        return self._request_json(
            method="GET",
            path=f"/dashboards/agents/{agent_code}",
            params={
                "scenario_id": scenario_id,
                "recent_alert_limit": recent_alert_limit,
            },
        )

    def operations_dashboard(
        self,
        *,
        scenario_id: str | None = None,
        recent_alert_limit: int = 10,
    ) -> dict[str, Any]:
        """Return the Operations stakeholder dashboard."""

        return self._request_json(
            method="GET",
            path="/dashboards/operations",
            params={
                "scenario_id": scenario_id,
                "recent_alert_limit": recent_alert_limit,
            },
        )

    def provider_dashboard(
        self,
        provider_code: str,
        *,
        scenario_id: str | None = None,
        recent_alert_limit: int = 10,
    ) -> dict[str, Any]:
        """Return one provider stakeholder dashboard."""

        return self._request_json(
            method="GET",
            path=f"/dashboards/providers/{provider_code}",
            params={
                "scenario_id": scenario_id,
                "recent_alert_limit": recent_alert_limit,
            },
        )

    def management_dashboard(
        self,
        *,
        scenario_id: str | None = None,
    ) -> dict[str, Any]:
        """Return the management oversight dashboard."""

        return self._request_json(
            method="GET",
            path="/dashboards/management",
            params={"scenario_id": scenario_id},
        )

    def evaluation_dashboard(self) -> dict[str, Any]:
        """Return controlled evaluation benchmark metrics."""

        return self._request_json(
            method="GET",
            path="/dashboards/evaluation",
        )
