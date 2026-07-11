"""Tests for the frontend FastAPI client."""

import httpx
import pytest

from frontend.api.client import (
    BackendAPIError,
    BackendClient,
)


def test_health_returns_backend_json() -> None:
    """The health method should return a JSON object."""

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/health"

        return httpx.Response(
            status_code=200,
            json={
                "status": "ok",
            },
        )

    client = BackendClient(
        base_url="http://backend.test",
        transport=httpx.MockTransport(
            handler
        ),
    )

    try:
        result = client.health()
    finally:
        client.close()

    assert result == {
        "status": "ok",
    }


def test_health_raises_clear_error_for_backend_failure(
) -> None:
    """Backend HTTP errors should become frontend errors."""

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=503,
            json={
                "detail": (
                    "Backend temporarily unavailable."
                ),
            },
            request=request,
        )

    client = BackendClient(
        base_url="http://backend.test",
        transport=httpx.MockTransport(
            handler
        ),
    )

    try:
        with pytest.raises(
            BackendAPIError,
            match="HTTP 503",
        ):
            client.health()
    finally:
        client.close()


def test_empty_backend_url_is_rejected() -> None:
    """A missing backend URL should fail immediately."""

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        BackendClient(
            base_url="   ",
        )


def test_list_alerts_drops_empty_query_params() -> None:
    """None and blank filters should not be sent to FastAPI."""

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/alerts"
        assert "status" not in request.url.params
        assert "agent_code" not in request.url.params
        assert request.url.params["limit"] == "25"

        return httpx.Response(
            status_code=200,
            json={
                "items": [],
                "total": 0,
                "limit": 25,
                "offset": 0,
            },
        )

    client = BackendClient(
        base_url="http://backend.test",
        transport=httpx.MockTransport(handler),
    )

    try:
        result = client.list_alerts(
            status="",
            agent_code=None,
            limit=25,
        )
    finally:
        client.close()

    assert result["total"] == 0


def test_operations_dashboard_uses_expected_path() -> None:
    """Dashboard helpers should call the mounted FastAPI routes."""

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/dashboards/operations"

        return httpx.Response(
            status_code=200,
            json={
                "summary": {},
                "agent_risks": [],
                "recent_alerts": [],
                "scenario_id": None,
                "last_updated_at": None,
                "generated_at": "2026-01-01T00:00:00Z",
                "synthetic_data_notice": "synthetic",
            },
        )

    client = BackendClient(
        base_url="http://backend.test",
        transport=httpx.MockTransport(handler),
    )

    try:
        result = client.operations_dashboard()
    finally:
        client.close()

    assert result["synthetic_data_notice"] == "synthetic"


def test_connect_error_mentions_base_url() -> None:
    """Connection failures should mention the configured backend."""

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        raise httpx.ConnectError(
            "connection refused",
            request=request,
        )

    client = BackendClient(
        base_url="http://127.0.0.1:8000",
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(
            BackendAPIError,
            match="127.0.0.1:8000",
        ):
            client.health()
    finally:
        client.close()
