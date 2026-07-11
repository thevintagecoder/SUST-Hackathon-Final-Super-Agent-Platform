"""Data-provider interface for mock and API modes."""

from __future__ import annotations

from typing import Protocol


class DataProvider(Protocol):
    """Contract implemented by mock and API data providers."""

    def get_overview(self) -> dict:
        """Return the operations overview payload."""

    def get_liquidity(self, agent_code: str) -> dict:
        """Return liquidity positions for one agent."""

    def list_alerts(self) -> list[dict]:
        """Return open and recent alerts."""

    def get_case(self, case_id: int) -> dict:
        """Return one case with timeline events."""

    def acknowledge_alert(self, alert_id: int, actor: str) -> dict:
        """Acknowledge one alert."""

    def add_case_note(self, case_id: int, actor: str, note: str) -> dict:
        """Append a note to one case timeline."""

    def update_case_status(self, case_id: int, status: str) -> dict:
        """Update one case status and append a timeline event."""

    def assign_case(self, case_id: int, owner: str) -> dict:
        """Assign one case to a new owner and append a timeline event."""
