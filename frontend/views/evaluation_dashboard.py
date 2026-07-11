"""Evaluation / benchmark dashboard view."""

from __future__ import annotations

import streamlit as st

from frontend.api.client import BackendClient
from frontend.components.common import (
    metric_row,
    render_technical_detail,
    run_api_call,
    safety_notice,
)


def render_evaluation_dashboard(client: BackendClient) -> None:
    """Render controlled evaluation benchmark metrics."""

    st.header("Model checks")
    safety_notice(
        "These metrics come from controlled synthetic "
        "benchmarks. They do not claim production accuracy."
    )

    data = run_api_call(
        "Loading evaluation metrics…",
        client.evaluation_dashboard,
    )

    if data is None:
        return

    st.subheader(
        f"{data.get('benchmark_id', 'Benchmark')} · "
        f"{data.get('dataset_type', 'synthetic')}"
    )

    forecast = data.get("forecast", {})
    anomaly = data.get("anomaly", {})

    st.markdown("#### Forecast benchmark")
    metric_row(
        [
            (
                "Predicted runway (h)",
                forecast.get("predicted_runway_hours"),
            ),
            (
                "Actual breach (h)",
                forecast.get("actual_breach_hours"),
            ),
            (
                "Abs error (h)",
                forecast.get("absolute_error_hours"),
            ),
            (
                "Warning lead time (h)",
                forecast.get("warning_lead_time_hours"),
            ),
            (
                "Passed",
                "Yes" if forecast.get("benchmark_passed") else "No",
            ),
        ]
    )

    st.markdown("#### Anomaly benchmark")
    metric_row(
        [
            ("True positive", anomaly.get("true_positive")),
            ("True negative", anomaly.get("true_negative")),
            ("False positive", anomaly.get("false_positive")),
            ("False negative", anomaly.get("false_negative")),
        ]
    )
    metric_row(
        [
            ("Precision", anomaly.get("precision")),
            ("Recall", anomaly.get("recall")),
            (
                "False positive rate",
                anomaly.get("false_positive_rate"),
            ),
            (
                "Passed",
                "Yes" if anomaly.get("benchmark_passed") else "No",
            ),
        ]
    )

    st.subheader("Responsible AI checks")
    checks = data.get("responsible_ai_checks", {})
    if checks:
        for key, value in checks.items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    else:
        st.caption("No responsible-AI checks were returned.")

    limitations = data.get("limitations", [])
    if limitations:
        st.subheader("Limitations")
        for item in limitations:
            st.write(f"- {item}")

    render_technical_detail(data)
