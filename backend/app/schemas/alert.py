"""Schemas shared by the multilingual alert system."""

from typing import Literal

from pydantic import BaseModel


AlertType = Literal[
    "LIQUIDITY_RUNWAY",
    "ANOMALY_REVIEW",
    "STALE_DATA",
    "SERVICEABILITY_SHORTFALL",
]


class LocalizedAlertText(BaseModel):
    """Store one alert message in three supported languages."""

    en: str
    bn: str
    bn_latn: str


class RenderedAlertTemplate(BaseModel):
    """Store the localized presentation text for one alert."""

    alert_type: AlertType

    title: LocalizedAlertText
    message: LocalizedAlertText
    next_step: LocalizedAlertText