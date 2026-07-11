"""Case management page with timeline and safe action forms."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from frontend.components.timeline import render_timeline
from frontend.config import get_active_data_mode, get_provider

DEFAULT_CASE_ID = 501
DEFAULT_ALERT_ID = 101

st.title("Case Management")
st.caption(
    f"Acknowledgement, notes, escalation, and resolution tracking. "
    f"Data mode: **{get_active_data_mode()}**"
)

if get_active_data_mode() == "mock":
    if "mock_provider" not in st.session_state:
        st.session_state["mock_provider"] = get_provider()
    provider = st.session_state["mock_provider"]
else:
    provider = get_provider()

try:
    case = provider.get_case(DEFAULT_CASE_ID)
    alerts = provider.list_alerts()
except Exception as exc:
    st.error(str(exc))
    st.stop()

linked_alert = next(
    (alert for alert in alerts if alert["id"] == case["alert_id"]),
    None,
)

st.subheader(f"Case #{case['id']}")
info_cols = st.columns(3)
info_cols[0].metric("Status", case["status"].title())
info_cols[1].metric("Owner", case["owner"])
info_cols[2].metric("Linked alert", case["alert_id"])

if linked_alert:
    st.caption(linked_alert["title"])

st.divider()
st.subheader("Timeline")
render_timeline(case["timeline"])

st.divider()
st.subheader("Case actions")

action_cols = st.columns(2)

with action_cols[0]:
    st.markdown("**Acknowledge alert**")
    acknowledge_actor = st.text_input(
        "Actor",
        value="ops-user-01",
        key="ack_actor",
    )
    if st.button("Acknowledge linked alert", key="ack_button"):
        try:
            result = provider.acknowledge_alert(
                DEFAULT_ALERT_ID,
                acknowledge_actor,
            )
            st.success(result["message"])
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

with action_cols[1]:
    st.markdown("**Update case status**")
    new_status = st.selectbox(
        "Status",
        options=["investigating", "escalated", "resolved"],
        index=["investigating", "escalated", "resolved"].index(case["status"]),
        key="case_status",
    )
    if st.button("Update status", key="status_button"):
        try:
            result = provider.update_case_status(DEFAULT_CASE_ID, new_status)
            st.success(result["message"])
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

st.markdown("**Add case note**")
note_actor = st.text_input("Note author", value="ops-user-01", key="note_actor")
note_text = st.text_area(
    "Note",
    placeholder="Add operational context for the review team.",
    key="note_text",
)
if st.button("Add note", key="note_button"):
    try:
        result = provider.add_case_note(
            DEFAULT_CASE_ID,
            note_actor,
            note_text,
        )
        st.success(result["message"])
        st.rerun()
    except Exception as exc:
        st.error(str(exc))

st.caption(
    "Actions update the in-memory mock timeline during demonstration. "
    "In API mode, the same forms call FastAPI endpoints."
)
