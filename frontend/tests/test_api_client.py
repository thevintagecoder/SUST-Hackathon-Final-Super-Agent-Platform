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