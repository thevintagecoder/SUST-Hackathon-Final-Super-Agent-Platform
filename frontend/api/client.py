"""HTTP client for communication with the FastAPI backend."""

from __future__ import annotations

from typing import Any

import httpx


DEFAULT_TIMEOUT_SECONDS = 5.0


class BackendAPIError(RuntimeError):
    """Raised when the frontend cannot use the backend API."""


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
                params=params,
                json=json,
            )

            response.raise_for_status()

        except httpx.TimeoutException as error:
            raise BackendAPIError(
                "The backend request timed out."
            ) from error

        except httpx.ConnectError as error:
            raise BackendAPIError(
                "The frontend could not connect to FastAPI. "
                "Confirm that the backend is running."
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

        if not isinstance(
            response_data,
            dict,
        ):
            raise BackendAPIError(
                "The backend response must be a JSON object."
            )

        return response_data

    def health(
        self,
    ) -> dict[str, Any]:
        """Return the backend health response."""

        return self._request_json(
            method="GET",
            path="/health",
        )