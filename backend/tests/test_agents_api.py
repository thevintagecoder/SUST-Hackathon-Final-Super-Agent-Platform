"""Tests for the Agent creation API."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app


test_engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Provide a client with an isolated test database."""

    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)

    def override_get_db() -> Iterator[Session]:
        with TestingSessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_create_agent_returns_201(
    client: TestClient,
) -> None:
    """A valid Agent request should be persisted."""

    response = client.post(
        "/agents",
        json={
            "code": "AGENT-TEST-001",
            "name": "Synthetic Test Outlet",
            "area": "Test Area",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert isinstance(body["id"], int)
    assert body["code"] == "AGENT-TEST-001"
    assert body["name"] == "Synthetic Test Outlet"
    assert body["area"] == "Test Area"
    assert body["is_active"] is True
    assert body["created_at"] is not None


def test_create_agent_rejects_duplicate_code(
    client: TestClient,
) -> None:
    """A duplicate Agent code should return HTTP 409."""

    payload = {
        "code": "AGENT-TEST-002",
        "name": "First Synthetic Outlet",
        "area": "Test Area",
    }

    first_response = client.post(
        "/agents",
        json=payload,
    )
    second_response = client.post(
        "/agents",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Agent code already exists."
    }


def test_create_agent_rejects_invalid_code(
    client: TestClient,
) -> None:
    """An invalid code format should return HTTP 422."""

    response = client.post(
        "/agents",
        json={
            "code": "invalid code",
            "name": "Synthetic Test Outlet",
            "area": "Test Area",
        },
    )

    assert response.status_code == 422