"""Tests for the database health endpoint."""

import pytest
from fastapi.testclient import TestClient
from psycopg import OperationalError

from backend.app.main import app


client = TestClient(app)


def test_database_health_returns_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return 200 when PostgreSQL responds successfully."""

    monkeypatch.setattr(
        "backend.app.main.check_database_connection",
        lambda: True,
    )

    response = client.get("/health/database")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "reachable",
    }


def test_database_health_returns_503_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return 503 when PostgreSQL cannot be reached."""

    def raise_connection_error() -> bool:
        raise OperationalError(
            "Simulated database connection failure"
        )

    monkeypatch.setattr(
        "backend.app.main.check_database_connection",
        raise_connection_error,
    )

    response = client.get("/health/database")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database is unavailable."
    }