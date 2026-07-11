"""Admin Case Management: alert table, coordination actions, case history."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from frontend.components.timeline import render_timeline
from frontend.config import get_active_data_mode, get_provider

DEFAULT_CASE_ID = 501

st.title("Admin Case Management")
st.caption(
    f"Assign, acknowledge, escalate, and resolve — every action is "
    f"recorded in the case history. Data mode: **{get_active_data_mode()}**"
)

if get_active_data_mode() == "mock":
    if "mock_provider" not in st.session_state:
        st.session_state["mock_provider"] = get_provider()
    provider = st.session_state["mock_provider"]
else:
    provider = get_provider()

try:
    alerts = provider.list_alerts()
    case = provider.get_case(DEFAULT_CASE_ID)
except Exception as exc:
    st.error(str(exc))
    if get_active_data_mode() == "api":
        st.info(
            "The backend appears unavailable. Restart with DATA_MODE=mock "
            "to preview the workflow without FastAPI."
        )
    st.stop()

st.subheader("Alert queue")
if not alerts:
    st.info("No alerts are open for review.")
else:
    alert_frame = pd.DataFrame(
        [
            {
                "ID": alert["id"],
                "Severity": alert["severity"],
                "Status": alert["status"].replace("_", " "),
                "Title": alert["title"],
                "Confidence": f"{alert['confidence'] * 100:.0f}%",
                "Owner": alert["owner"],
                "Created": alert["created_at"],
            }
            for alert in alerts
        ]
    )
    st.dataframe(alert_frame, hide_index=True, use_container_width=True)

st.divider()
st.subheader(f"Case #{case['id']}")

linked_alert = next(
    (alert for alert in alerts if alert["id"] == case["alert_id"]),
    None,
)
info_cols = st.columns(3)
info_cols[0].metric("Status", case["status"].title())
info_cols[1].metric("Owner", case["owner"])
info_cols[2].metric("Linked alert", case["alert_id"])
if linked_alert:
    st.caption(linked_alert["title"])

st.divider()
st.subheader("Coordination actions")

assign_col, ack_col = st.columns(2)

with assign_col:
    st.markdown("**Assign case**")
    new_owner = st.text_input(
        "New owner",
        value=case["owner"],
        key="assign_owner",
    )
    if st.button("Assign", key="assign_button"):
        try:
            result = provider.assign_case(case["id"], new_owner)
            st.success(result["message"])
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

with ack_col:
    st.markdown("**Acknowledge linked alert**")
    acknowledge_actor = st.text_input(
        "Actor",
        value="ops-user-01",
        key="ack_actor",
    )
    if st.button("Acknowledge", key="ack_button"):
        try:
            result = provider.acknowledge_alert(
                case["alert_id"],
                acknowledge_actor,
            )
            st.success(result["message"])
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

escalate_col, resolve_col = st.columns(2)

with escalate_col:
    st.markdown("**Escalate case**")
    if st.button("Escalate", key="escalate_button"):
        try:
            result = provider.update_case_status(case["id"], "escalated")
            st.success(result["message"])
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

with resolve_col:
    st.markdown("**Resolve case**")
    if st.button("Resolve", key="resolve_button"):
        try:
            result = provider.update_case_status(case["id"], "resolved")
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
        result = provider.add_case_note(case["id"], note_actor, note_text)
        st.success(result["message"])
        st.rerun()
    except Exception as exc:
        st.error(str(exc))

st.divider()
st.subheader("Case history")
st.caption(
    "Append-only log of every assignment, acknowledgement, status change, "
    "and note on this case."
)
render_timeline(case["timeline"])

st.caption(
    "Actions update the in-memory mock timeline during demonstration. "
    "In API mode, the same forms call FastAPI endpoints."
)
