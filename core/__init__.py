"""Shared analytics package for the Super Agent platform.

Pure-Python liquidity forecasting, anomaly detection, risk scoring, and
narrative generation. Contains no Streamlit or FastAPI imports so both
the dashboard and the backend can reuse the same logic.
"""

from core.data_access import DataUnavailableError, DemoDataRepository, ScenarioInfo
from core.forecast import ProviderForecast, forecast_provider, forecast_scenario
from core.anomaly import AnomalyFlag, detect_anomalies
from core.risk import RiskAssessment, RiskComponent, assess_agent_risk
from core.narrative import forecast_narrative, risk_narrative

__all__ = [
    "AnomalyFlag",
    "DataUnavailableError",
    "DemoDataRepository",
    "ProviderForecast",
    "RiskAssessment",
    "RiskComponent",
    "ScenarioInfo",
    "assess_agent_risk",
    "detect_anomalies",
    "forecast_narrative",
    "forecast_provider",
    "forecast_scenario",
    "risk_narrative",
]
