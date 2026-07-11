"""API tests for Agent-to-Agent support discovery."""

from decimal import Decimal
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.data_loading.synthetic_loader import (
    load_synthetic_scenario,
)
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.routers.network import router
from synthetic_data.generator import generate_bundle


@pytest.fixture
def test_client(
    tmp_path: Path,
):
    """Create an API backed by the NETWORK-001 scenario."""

    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    testing_session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(engine)

    generated_directory = (
        tmp_path / "generated"
    )

    generate_bundle(
        output_directory=generated_directory,
        seed=42,
    )

    with testing_session_factory() as db:
        load_synthetic_scenario(
            db=db,
            input_directory=(
                generated_directory
            ),
            scenario_id="NETWORK-001",
        )

    def override_get_db():
        db = testing_session_factory()

        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(app) as client:
        yield client

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_cash_in_recommends_fresh_nagad_candidate(
    test_client: TestClient,
) -> None:
    """Fresh same-provider capacity should rank first."""

    response = test_client.post(
        "/network/find-support",
        json={
            "requesting_agent_code": (
                "AGENT-SYL-001"
            ),
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_in",
            "amount": 80000,
            "max_distance_km": 10,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["status"]
        == "NETWORK_SUPPORT_AVAILABLE"
    )
    assert body["local_serviceable"] is False

    assert Decimal(
        str(body["local_available_amount"])
    ) == Decimal("20000.00")

    assert Decimal(
        str(body["shortfall"])
    ) == Decimal("60000.00")

    assert body["candidates"]

    first_candidate = body["candidates"][0]

    assert (
        first_candidate["agent_code"]
        == "AGENT-SYL-002"
    )
    assert (
        first_candidate[
            "recommendation_status"
        ]
        == "RECOMMENDED"
    )
    assert (
        first_candidate[
            "freshness_state"
        ]
        == "fresh"
    )
    assert Decimal(
        str(
            first_candidate[
                "supportable_capacity"
            ]
        )
    ) == Decimal("80000.00")


def test_delayed_candidate_requires_confirmation(
    test_client: TestClient,
) -> None:
    """Delayed capacity must not be treated as confirmed."""

    response = test_client.post(
        "/network/find-support",
        json={
            "requesting_agent_code": (
                "AGENT-SYL-001"
            ),
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_in",
            "amount": 80000,
        },
    )

    assert response.status_code == 200

    body = response.json()

    stale_candidate = next(
        candidate
        for candidate in body["candidates"]
        if (
            candidate["agent_code"]
            == "AGENT-SYL-004"
        )
    )

    assert (
        stale_candidate[
            "recommendation_status"
        ]
        == "REQUIRES_CONFIRMATION"
    )
    assert (
        stale_candidate[
            "freshness_state"
        ]
        == "delayed"
    )
    assert (
        stale_candidate[
            "can_cover_shortfall"
        ]
        is True
    )


def test_cash_out_recommends_high_cash_agent(
    test_client: TestClient,
) -> None:
    """A cash-out should search physical-cash capacity."""

    response = test_client.post(
        "/network/find-support",
        json={
            "requesting_agent_code": (
                "AGENT-SYL-001"
            ),
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_out",
            "amount": 80000,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["local_serviceable"] is False

    assert Decimal(
        str(body["shortfall"])
    ) == Decimal("55000.00")

    assert body["candidates"]

    first_candidate = body["candidates"][0]

    assert (
        first_candidate["agent_code"]
        == "AGENT-SYL-003"
    )
    assert (
        first_candidate[
            "recommendation_status"
        ]
        == "RECOMMENDED"
    )
    assert Decimal(
        str(
            first_candidate[
                "supportable_capacity"
            ]
        )
    ) == Decimal("100000.00")


def test_locally_serviceable_request_returns_no_candidates(
    test_client: TestClient,
) -> None:
    """Do not search the network when local capacity is enough."""

    response = test_client.post(
        "/network/find-support",
        json={
            "requesting_agent_code": (
                "AGENT-SYL-001"
            ),
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_in",
            "amount": 10000,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["status"]
        == "LOCAL_SERVICEABLE"
    )
    assert body["local_serviceable"] is True
    assert body["shortfall"] == "0.00"
    assert body["candidates"] == []


def test_unknown_requesting_agent_returns_404(
    test_client: TestClient,
) -> None:
    """An unknown requesting Agent should fail clearly."""

    response = test_client.post(
        "/network/find-support",
        json={
            "requesting_agent_code": (
                "AGENT-UNKNOWN"
            ),
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_in",
            "amount": 80000,
        },
    )

    assert response.status_code == 404


def test_invalid_amount_returns_422(
    test_client: TestClient,
) -> None:
    """The requested amount must be positive."""

    response = test_client.post(
        "/network/find-support",
        json={
            "requesting_agent_code": (
                "AGENT-SYL-001"
            ),
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_in",
            "amount": 0,
        },
    )

    assert response.status_code == 422