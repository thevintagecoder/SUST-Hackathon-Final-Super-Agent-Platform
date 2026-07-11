"""Tests for the API health endpoint."""

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_check_returns_ok() -> None:
    """The health endpoint should confirm that the API is running."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_rejects_post_requests() -> None:
    """The health endpoint should not accept an unsupported HTTP method."""

    response = client.post("/health")

    assert response.status_code == 405
    assert response.json()["detail"] == "Method Not Allowed"