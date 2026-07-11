"""Frontend configuration and data-provider factory."""

from __future__ import annotations

import os
from pathlib import Path

from frontend.data.api_provider import ApiDataProvider
from frontend.data.mock_provider import MockDataProvider
from frontend.data.provider import DataProvider

FRONTEND_ROOT = Path(__file__).resolve().parent
MOCK_DATA_DIR = FRONTEND_ROOT / "mock_data"

VALID_DATA_MODES = frozenset({"mock", "api"})

_raw_mode = os.environ.get("DATA_MODE", "mock").strip().lower()
DATA_MODE = _raw_mode if _raw_mode in VALID_DATA_MODES else "mock"

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_TIMEOUT_SECONDS = 3


def get_active_data_mode() -> str:
    """Return the configured data mode ('mock' or 'api')."""

    return DATA_MODE


def get_provider() -> DataProvider:
    """Return the data provider for the configured mode."""

    if DATA_MODE == "api":
        return ApiDataProvider(
            base_url=API_BASE_URL,
            timeout_seconds=API_TIMEOUT_SECONDS,
        )

    return MockDataProvider(mock_data_dir=MOCK_DATA_DIR)
