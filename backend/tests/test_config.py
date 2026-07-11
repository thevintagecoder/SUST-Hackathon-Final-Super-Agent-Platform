"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings


def test_settings_have_safe_defaults() -> None:
    """Settings should work without requiring a local .env file."""

    settings = Settings(_env_file=None)

    assert settings.name == (
        "Super Agent Liquidity & Risk Intelligence API"
    )
    assert settings.environment == "development"
    assert settings.version == "0.1.0"
    assert settings.debug is False


def test_environment_variables_override_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment variables should override default configuration."""

    monkeypatch.setenv("APP_ENVIRONMENT", "testing")
    monkeypatch.setenv("APP_VERSION", "0.2.0")
    monkeypatch.setenv("APP_DEBUG", "true")

    settings = Settings(_env_file=None)

    assert settings.environment == "testing"
    assert settings.version == "0.2.0"
    assert settings.debug is True


def test_invalid_environment_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unsupported environment name should fail validation."""

    monkeypatch.setenv("APP_ENVIRONMENT", "unknown-environment")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)