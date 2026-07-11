"""API tests for the support-request coordination workflow."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.models import Agent, Provider
from backend.app.routers.support_requests import router


def create_test_client() -> tuple[
    TestClient,
    sessionmaker,
    object,
]:
    """Create an isolated API and database."""

    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(engine)

    with session_factory() as db:
        db.add_all(
            [
                Agent(
                    code="AGENT-SYL-001",
                    name="Synthetic Requesting Agent",
                    area="Sylhet",
                ),
                Agent(
                    code="AGENT-SYL-002",
                    name="Synthetic Supporting Agent",
                    area="Sylhet",
                ),
                Provider(
                    code="NAGAD_SIM",
                    name="Synthetic Nagad Provider",
                ),
            ]
        )
        db.commit()

    def override_get_db():
        db = session_factory()

        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[
        get_db
    ] = override_get_db

    return (
        TestClient(app),
        session_factory,
        engine,
    )


def create_request(
    client: TestClient,
) -> dict:
    """Create one pending support request."""

    response = client.post(
        "/support-requests",
        json={
            "requesting_agent_code": "AGENT-SYL-001",
            "supporting_agent_code": "AGENT-SYL-002",
            "provider_code": "NAGAD_SIM",
            "transaction_type": "cash_in",
            "requested_amount": 60000,
            "reason": (
                "Requesting Agent has insufficient Nagad "
                "electronic float."
            ),
            "created_by": "AGENT-SYL-001",
            "operations_owner": "SYLHET-OPERATIONS",
        },
    )

    assert response.status_code == 201

    return response.json()


def test_support_request_is_created_with_timeline() -> None:
    """A new request should begin in pending state."""

    client, _, engine = create_test_client()

    try:
        body = create_request(client)

        assert body["status"] == "pending"
        assert body["requested_amount"] == "60000.00"
        assert body["approved_amount"] is None
        assert body["resource_type"] == "provider_float"

        assert len(body["events"]) == 1
        assert body["events"][0]["event_type"] == "created"
        assert body["events"][0]["to_status"] == "pending"

    finally:
        client.close()
        engine.dispose()


def test_supporting_agent_can_accept_request() -> None:
    """The supporting Agent should be able to accept."""

    client, _, engine = create_test_client()

    try:
        created = create_request(client)

        response = client.post(
            f"/support-requests/{created['id']}/accept",
            json={
                "actor_code": "AGENT-SYL-002",
                "approved_amount": 60000,
                "note": "Capacity confirmed by supporting Agent.",
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["status"] == "accepted"
        assert body["approved_amount"] == "60000.00"

        event_types = [
            event["event_type"]
            for event in body["events"]
        ]

        assert event_types == [
            "created",
            "accepted",
        ]

    finally:
        client.close()
        engine.dispose()


def test_supporting_agent_can_reject_request() -> None:
    """A pending request may be rejected."""

    client, _, engine = create_test_client()

    try:
        created = create_request(client)

        response = client.post(
            f"/support-requests/{created['id']}/reject",
            json={
                "actor_code": "AGENT-SYL-002",
                "note": "Current capacity is no longer available.",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "rejected"

    finally:
        client.close()
        engine.dispose()


def test_operations_can_escalate_and_resolve() -> None:
    """Operations should control escalation and resolution."""

    client, _, engine = create_test_client()

    try:
        created = create_request(client)

        escalation = client.post(
            f"/support-requests/{created['id']}/escalate",
            json={
                "actor_code": "SYLHET-OPERATIONS",
                "note": "Provider coordination is required.",
            },
        )

        assert escalation.status_code == 200
        assert escalation.json()["status"] == "escalated"

        resolution = client.post(
            f"/support-requests/{created['id']}/resolve",
            json={
                "actor_code": "SYLHET-OPERATIONS",
                "note": (
                    "Customer was referred to an Agent with "
                    "confirmed capacity."
                ),
            },
        )

        assert resolution.status_code == 200

        body = resolution.json()

        assert body["status"] == "resolved"

        event_types = [
            event["event_type"]
            for event in body["events"]
        ]

        assert event_types == [
            "created",
            "escalated",
            "resolved",
        ]

    finally:
        client.close()
        engine.dispose()


def test_operations_can_monitor_requests() -> None:
    """Operations should be able to list the request queue."""

    client, _, engine = create_test_client()

    try:
        created = create_request(client)

        client.post(
            f"/support-requests/{created['id']}/accept",
            json={
                "actor_code": "AGENT-SYL-002",
                "approved_amount": 50000,
                "note": "Partial support accepted.",
            },
        )

        response = client.get(
            "/support-requests",
            params={
                "status": "accepted",
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["total"] == 1
        assert body["items"][0]["status"] == "accepted"

    finally:
        client.close()
        engine.dispose()


def test_invalid_transition_returns_conflict() -> None:
    """An accepted request cannot be accepted again."""

    client, _, engine = create_test_client()

    try:
        created = create_request(client)

        first_response = client.post(
            f"/support-requests/{created['id']}/accept",
            json={
                "actor_code": "AGENT-SYL-002",
                "approved_amount": 60000,
            },
        )

        assert first_response.status_code == 200

        second_response = client.post(
            f"/support-requests/{created['id']}/accept",
            json={
                "actor_code": "AGENT-SYL-002",
                "approved_amount": 60000,
            },
        )

        assert second_response.status_code == 409

    finally:
        client.close()
        engine.dispose()


def test_note_is_added_without_changing_status() -> None:
    """A note should extend the timeline without a transition."""

    client, _, engine = create_test_client()

    try:
        created = create_request(client)

        response = client.post(
            f"/support-requests/{created['id']}/notes",
            json={
                "actor_code": "SYLHET-OPERATIONS",
                "actor_role": "operations",
                "note": "Supporting Agent has been contacted.",
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["status"] == "pending"
        assert body["events"][-1]["event_type"] == "note_added"
        assert (
            body["events"][-1]["note"]
            == "Supporting Agent has been contacted."
        )

    finally:
        client.close()
        engine.dispose()