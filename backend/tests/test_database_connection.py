"""Tests for low-level PostgreSQL connectivity checks."""

from unittest.mock import MagicMock

import pytest
from psycopg import OperationalError

from backend.app.core.config import Settings
from backend.app.db.connection import (
    check_database_connection,
    main,
)


@pytest.mark.parametrize(
    ("query_result", "expected"),
    [
        ((1,), True),
        ((0,), False),
    ],
)
def test_check_database_connection_uses_select_one(
    monkeypatch: pytest.MonkeyPatch,
    query_result: tuple[int],
    expected: bool,
) -> None:
    """Return whether PostgreSQL produced the expected result."""

    settings = Settings(
        _env_file=None,
        database_host="database.example.test",
        database_port=6543,
        database_name="test_database",
        database_user="test_user",
        database_password="test-password",
        database_connect_timeout_seconds=5,
    )

    cursor = MagicMock()
    cursor.fetchone.return_value = query_result

    cursor_context = MagicMock()
    cursor_context.__enter__.return_value = cursor

    connection = MagicMock()
    connection.cursor.return_value = cursor_context

    connection_context = MagicMock()
    connection_context.__enter__.return_value = connection

    connect_mock = MagicMock(
        return_value=connection_context,
    )

    monkeypatch.setattr(
        "backend.app.db.connection.psycopg.connect",
        connect_mock,
    )

    result = check_database_connection(settings)

    assert result is expected
    cursor.execute.assert_called_once_with("SELECT 1;")
    connect_mock.assert_called_once_with(
        host="database.example.test",
        port=6543,
        dbname="test_database",
        user="test_user",
        password="test-password",
        connect_timeout=5,
    )


def test_main_prints_success_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The terminal check should report a successful connection."""

    monkeypatch.setattr(
        "backend.app.db.connection.check_database_connection",
        lambda: True,
    )

    main()

    output = capsys.readouterr().out

    assert output == (
        "Database connection successful: "
        "SELECT 1 returned 1.\n"
    )


def test_main_exits_for_unexpected_query_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The terminal check should fail for an unexpected result."""

    monkeypatch.setattr(
        "backend.app.db.connection.check_database_connection",
        lambda: False,
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert capsys.readouterr().out == (
        "Database connection failed: "
        "unexpected SELECT 1 result.\n"
    )


def test_main_exits_when_postgresql_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The terminal check should handle a Psycopg connection error."""

    def raise_connection_error() -> bool:
        raise OperationalError(
            "Simulated PostgreSQL connection failure"
        )

    monkeypatch.setattr(
        "backend.app.db.connection.check_database_connection",
        raise_connection_error,
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert capsys.readouterr().out == (
        "Database connection failed: OperationalError\n"
    )