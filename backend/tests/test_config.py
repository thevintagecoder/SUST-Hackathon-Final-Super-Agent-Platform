"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings


def test_settings_have_safe_defaults() -> None:
    """Settings should have predictable development defaults."""

    settings = Settings(_env_file=None)

    assert settings.name == (
        "Super Agent Liquidity & Risk Intelligence API"
    )
    assert settings.environment == "development"
    assert settings.version == "0.1.0"
    assert settings.debug is False

    assert settings.database_host == "127.0.0.1"
    assert settings.database_port == 5432
    assert settings.database_name == "super_agent"
    assert settings.database_user == "super_agent_user"
    assert (
        settings.database_password.get_secret_value()
        == "local-development-only"
    )
    assert settings.database_connect_timeout_seconds == 3


def test_environment_variables_override_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment variables should override default values."""

    monkeypatch.setenv("APP_ENVIRONMENT", "testing")
    monkeypatch.setenv("APP_VERSION", "0.2.0")
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("APP_DATABASE_PORT", "6543")
    monkeypatch.setenv(
        "APP_DATABASE_PASSWORD",
        "test-password",
    )

    settings = Settings(_env_file=None)

    assert settings.environment == "testing"
    assert settings.version == "0.2.0"
    assert settings.debug is True
    assert settings.database_port == 6543
    assert (
        settings.database_password.get_secret_value()
        == "test-password"
    )


def test_invalid_environment_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unsupported environment should fail validation."""

    monkeypatch.setenv(
        "APP_ENVIRONMENT",
        "unknown-environment",
    )

    with pytest.raises(ValidationError):
        Settings(_env_file=None)