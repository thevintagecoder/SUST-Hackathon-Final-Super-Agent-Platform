"""Plain-language narratives (English and Bangla) for dashboard panels.

Narratives always hedge appropriately ("may run low", "for review") and
never use fraud language. Both languages are generated from the same
underlying numbers so they can never disagree.
"""

from __future__ import annotations

import math

from core.forecast import ProviderForecast
from core.risk import RiskAssessment

SUPPORTED_LANGUAGES = ("en", "bn")

RISK_LEVEL_LABELS = {
    "en": {"low": "low", "elevated": "elevated", "high": "high"},
    "bn": {"low": "কম", "elevated": "মাঝারি", "high": "উচ্চ"},
}


def _check_language(language: str) -> None:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{language}'. "
            f"Expected one of {SUPPORTED_LANGUAGES}."
        )


def forecast_narrative(forecast: ProviderForecast, language: str = "en") -> str:
    """One plain-language sentence panel for a provider forecast."""

    _check_language(language)
    confidence_pct = round(forecast.confidence * 100)

    if not math.isfinite(forecast.runway_hours):
        if language == "bn":
            return (
                f"{forecast.provider_code}-এর ব্যালেন্স বর্তমান লেনদেনের ধারায় "
                f"কমছে না। কোনো ঘাটতির পূর্বাভাস নেই (আস্থা {confidence_pct}%)।"
            )
        return (
            f"{forecast.provider_code} balance is not draining at the "
            f"current transaction pattern. No shortage is projected "
            f"(confidence {confidence_pct}%)."
        )

    low_time = forecast.projected_low_time
    low_time_text = (
        low_time.strftime("%H:%M UTC, %d %b") if low_time is not None else "—"
    )

    if forecast.is_below_warning:
        if language == "bn":
            return (
                f"{forecast.provider_code}-এর ফ্লোট আনুমানিক "
                f"{forecast.runway_hours:.1f} ঘণ্টার মধ্যে কম হয়ে যেতে পারে "
                f"(আনুমানিক সময় {low_time_text})। আস্থা {confidence_pct}%। "
                f"রিব্যালেন্সের প্রয়োজন আছে কি না তা পর্যালোচনা করুন।"
            )
        return (
            f"{forecast.provider_code} float may run low in about "
            f"{forecast.runway_hours:.1f} hours (around {low_time_text}), "
            f"confidence {confidence_pct}%. Review whether a rebalance "
            f"is needed."
        )

    if language == "bn":
        return (
            f"{forecast.provider_code}-এর আনুমানিক রানওয়ে "
            f"{forecast.runway_hours:.1f} ঘণ্টা — সতর্কসীমার "
            f"({forecast.warning_threshold_hours:.0f} ঘণ্টা) উপরে। "
            f"আস্থা {confidence_pct}%।"
        )
    return (
        f"{forecast.provider_code} has an estimated runway of "
        f"{forecast.runway_hours:.1f} hours, above the "
        f"{forecast.warning_threshold_hours:.0f}-hour warning threshold "
        f"(confidence {confidence_pct}%)."
    )


def risk_narrative(assessment: RiskAssessment, language: str = "en") -> str:
    """Plain-language summary of a composite risk assessment."""

    _check_language(language)
    level_label = RISK_LEVEL_LABELS[language][assessment.level]
    dominant = max(assessment.components, key=lambda item: item.weighted_score)
    flag_count = len(assessment.flags)

    if language == "bn":
        text = (
            f"এজেন্ট {assessment.agent_code}-এর সামগ্রিক পর্যালোচনা-অগ্রাধিকার "
            f"স্কোর {assessment.total_score:.0f}/১০০ ({level_label} স্তর)। "
            f"প্রধান কারণ: {dominant.detail} "
        )
        if flag_count:
            text += (
                f"{flag_count}টি অস্বাভাবিক-কার্যকলাপ ফ্ল্যাগ মানব পর্যালোচনার "
                f"অপেক্ষায় আছে। "
            )
        text += (
            "এই স্কোর শুধু পর্যালোচনার অগ্রাধিকার নির্ধারণের জন্য — এটি কোনো "
            "সিদ্ধান্ত বা অভিযোগ নয়।"
        )
        return text

    text = (
        f"Agent {assessment.agent_code} has a review-priority score of "
        f"{assessment.total_score:.0f}/100 ({level_label} level). "
        f"Main driver: {dominant.detail} "
    )
    if flag_count:
        text += (
            f"{flag_count} unusual-activity flag(s) are awaiting human "
            f"review. "
        )
    text += (
        "This score prioritises review only — it is not a determination "
        "or an accusation."
    )
    return text
