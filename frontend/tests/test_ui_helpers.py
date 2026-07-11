"""Tests for operator-facing data formatting helpers."""

from frontend.components.common import (
    agent_display_name,
    agent_options,
    alert_status_label,
    alert_type_label,
    freshness_label,
    localized_text,
    money,
    numeric_sum,
    provider_label,
    severity_label,
)


def test_money_formats_backend_decimal_strings() -> None:
    """Balance strings should be readable as Bangladeshi taka."""

    assert money("65000.00") == "৳65,000.00"
    assert money(None) == "—"


def test_numeric_sum_handles_missing_backend_values() -> None:
    """Portfolio totals should ignore missing or invalid balances."""

    assert numeric_sum(["65000.00", None, "bad", "55000"]) == 120000


def test_provider_labels_use_operator_names() -> None:
    """Synthetic provider codes should display as familiar brands."""

    assert provider_label("BKASH_SIM") == "bKash"
    assert provider_label("NAGAD_SIM") == "Nagad"


def test_freshness_label_explains_operational_risk() -> None:
    """Freshness values should tell operators whether to verify."""

    assert freshness_label("fresh") == "Live balance"
    # Stale label includes a warning symbol
    assert "stale" in freshness_label("stale").lower() or "verify" in freshness_label("stale").lower()


def test_localized_text_falls_back_to_english() -> None:
    """Missing selected language should fall back predictably."""

    assert (
        localized_text(
            {"en": "Review balance", "bn": "ব্যালেন্স দেখুন"},
            language="bn_latn",
        )
        == "Review balance"
    )


def test_localized_text_returns_bangla_when_selected() -> None:
    """Bangla selection should return Bengali script when available."""

    assert (
        localized_text(
            {"en": "Review balance", "bn": "ব্যালেন্স দেখুন"},
            language="bn",
        )
        == "ব্যালেন্স দেখুন"
    )


def test_agent_options_derive_from_live_operations_data() -> None:
    """Agent selectors should reflect the loaded backend scenario."""

    operations = {
        "agent_risks": [
            {"agent_code": "AGENT-SYL-004"},
            {"agent_code": "AGENT-SYL-002"},
        ]
    }

    assert agent_options(operations) == [
        "AGENT-SYL-004",
        "AGENT-SYL-002",
    ]


def test_alert_labels_hide_api_tokens() -> None:
    """Alert enums should map to operator-facing labels."""

    assert alert_type_label("SERVICEABILITY_SHORTFALL") == (
        "Cannot serve customer amount"
    )
    assert alert_status_label("OPEN") == "New \u2014 needs review"
    assert severity_label("HIGH") == "High"


def test_agent_display_name_uses_location_name() -> None:
    """The demo agent should show a recognisable branch name, not a raw code."""

    display = agent_display_name("AGENT-SYL-001")
    # Shows the branch name and still includes the code for traceability
    assert "Zindabazar" in display
    assert "AGENT-SYL-001" in display
