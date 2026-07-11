"""Streamlit entry point for the liquidity intelligence platform."""

from __future__ import annotations

import os
from typing import Any

import streamlit as st

from frontend.api.client import (
    BackendAPIError,
    BackendClient,
)


DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"


def get_backend_base_url() -> str:
    """Return the configured FastAPI base URL."""

    return os.getenv(
        "FASTAPI_BASE_URL",
        DEFAULT_BACKEND_URL,
    )


@st.cache_resource
def get_backend_client(
    base_url: str,
) -> BackendClient:
    """Create one shared backend API client."""

    return BackendClient(
        base_url=base_url,
    )


def render_health_response(
    health_data: dict[str, Any],
) -> None:
    """Display the backend connection result."""

    st.success(
        "Connected successfully to the FastAPI backend."
    )

    with st.expander(
        "View backend health response",
        expanded=False,
    ):
        st.json(
            health_data
        )


st.set_page_config(
    page_title=(
        "Super Agent Liquidity Intelligence"
    ),
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title(
    "Super Agent Liquidity & Risk Intelligence"
)

st.caption(
    "Decision-support platform using controlled "
    "synthetic data and human-reviewed alerts."
)

st.info(
    "This prototype does not move money, reserve funds, "
    "suspend Agents, or perform automatic enforcement."
)

st.divider()

st.subheader(
    "System connection"
)

backend_base_url = get_backend_base_url()

st.write(
    "FastAPI backend:"
)

st.code(
    backend_base_url,
    language=None,
)

backend_client = get_backend_client(
    backend_base_url
)

try:
    health_response = backend_client.health()

except BackendAPIError as error:
    st.error(
        str(error)
    )

    st.warning(
        "Start FastAPI in another terminal, then reload "
        "this Streamlit page."
    )

    st.code(
        "uvicorn backend.app.main:app --reload",
        language="bash",
    )

    st.stop()

render_health_response(
    health_response
)

st.divider()

st.subheader(
    "Frontend foundation ready"
)

st.write(
    "The Streamlit application is now communicating "
    "with FastAPI through the centralized API client."
)