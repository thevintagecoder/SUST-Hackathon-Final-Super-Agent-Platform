"""Tests for multilingual responsible alert templates."""

from decimal import Decimal

import pytest

from backend.app.services.alert_templates import (
    AlertTemplateError,
    render_alert_template,
)


def test_liquidity_alert_has_three_languages() -> None:
    """Liquidity warnings should include all languages."""

    result = render_alert_template(
        alert_type="LIQUIDITY_RUNWAY",
        provider_name="Nagad",
        runway_hours=Decimal("3.50"),
    )

    assert result.alert_type == "LIQUIDITY_RUNWAY"

    assert "Nagad" in result.title.en
    assert "Nagad" in result.title.bn
    assert "Nagad" in result.title.bn_latn

    assert "3.50" in result.message.en
    assert "৩.৫০" in result.message.bn
    assert "3.50" in result.message.bn_latn

    assert "human-approved" in (
        result.next_step.en
    )


def test_anomaly_alert_uses_responsible_language() -> None:
    """Anomaly text should request review without accusation."""

    result = render_alert_template(
        alert_type="ANOMALY_REVIEW",
    )

    combined_english_text = " ".join(
        (
            result.title.en,
            result.message.en,
            result.next_step.en,
        )
    ).lower()

    assert "requires review" in (
        combined_english_text
    )

    assert "legitimate explanation" in (
        combined_english_text
    )

    assert "confirmed fraud" not in (
        combined_english_text
    )

    assert "fraudulent agent" not in (
        combined_english_text
    )

    assert result.title.bn
    assert result.title.bn_latn


def test_stale_data_alert_requires_provider() -> None:
    """Stale-data alerts should identify the provider."""

    with pytest.raises(
        AlertTemplateError,
        match="provider_name",
    ):
        render_alert_template(
            alert_type="STALE_DATA",
        )


def test_stale_data_alert_warns_about_uncertainty() -> None:
    """Delayed data should not be presented as certain."""

    result = render_alert_template(
        alert_type="STALE_DATA",
        provider_name="bKash",
    )

    assert "may be uncertain" in (
        result.message.en
    )

    assert "অনিশ্চিত" in (
        result.message.bn
    )

    assert "onishchit" in (
        result.message.bn_latn
    )


def test_serviceability_alert_formats_shortfall() -> None:
    """Shortfall alerts should show evidence in all languages."""

    result = render_alert_template(
        alert_type=(
            "SERVICEABILITY_SHORTFALL"
        ),
        resource_name="Nagad float",
        shortfall_amount=Decimal(
            "12500.00"
        ),
    )

    assert "৳12500.00" in (
        result.message.en
    )

    assert "৳১২৫০০.০০" in (
        result.message.bn
    )

    assert "৳12500.00" in (
        result.message.bn_latn
    )

    assert "cannot currently be confirmed" in (
        result.message.en
    )


def test_negative_shortfall_is_rejected() -> None:
    """A resource shortfall cannot be negative."""

    with pytest.raises(
        AlertTemplateError,
        match="cannot be negative",
    ):
        render_alert_template(
            alert_type=(
                "SERVICEABILITY_SHORTFALL"
            ),
            resource_name="Physical cash",
            shortfall_amount=Decimal(
                "-1.00"
            ),
        )