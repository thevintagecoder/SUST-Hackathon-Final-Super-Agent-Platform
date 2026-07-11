"""Tests for SQLAlchemy database-session configuration."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.db.session import (
    SessionLocal,
    build_database_url,
    get_db,
)


def test_build_database_url_uses_settings() -> None:
    """Build the expected Psycopg PostgreSQL URL."""

    settings = Settings(
        _env_file=None,
        database_host="database.example.test",
        database_port=6543,
        database_name="test_database",
        database_user="test_user",
        database_password="test-password",
    )

    database_url = build_database_url(settings)

    assert database_url.drivername == "postgresql+psycopg"
    assert database_url.host == "database.example.test"
    assert database_url.port == 6543
    assert database_url.database == "test_database"
    assert database_url.username == "test_user"
    assert database_url.password == "test-password"


def test_session_local_creates_sqlalchemy_session() -> None:
    """The session factory should create a Session."""

    with SessionLocal() as session:
        assert isinstance(session, Session)


def test_get_db_yields_and_closes_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The FastAPI dependency should close its Session."""

    fake_session = MagicMock(
        spec=Session,
    )

    monkeypatch.setattr(
        "backend.app.db.session.SessionLocal",
        lambda: fake_session,
    )

    dependency = get_db()

    assert next(dependency) is fake_session

    with pytest.raises(StopIteration):
        next(dependency)

    fake_session.close.assert_called_once_with()