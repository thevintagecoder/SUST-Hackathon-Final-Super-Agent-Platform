"""Support-request coordination workflow view."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend.api.client import BackendClient
from frontend.components.common import (
    KNOWN_AGENT_CODES,
    KNOWN_PROVIDER_CODES,
    SAMPLE_AGENT_CODE,
    SUPPORT_STATUSES,
    TRANSACTION_TYPES,
    agent_display_name,
    optional_text,
    provider_label,
    render_technical_detail,
    run_api_call,
    safety_notice,
)


def render_support_requests(client: BackendClient) -> None:
    """Render support-request list, create, and workflow actions."""

    st.header("Support requests")
    st.markdown(
        '<div class="section-intro">'
        "When one agent is short on float, they can ask a nearby "
        "peer for temporary support. This is separate from risk alerts."
        "</div>",
        unsafe_allow_html=True,
    )
    safety_notice()

    tab_list, tab_create, tab_workflow = st.tabs(
        ["Browse", "Create", "Detail & actions"]
    )

    with tab_list:
        _render_list(client)

    with tab_create:
        _render_create(client)

    with tab_workflow:
        _render_workflow(client)


def _render_list(client: BackendClient) -> None:
    status = st.selectbox(
        "Filter by status",
        SUPPORT_STATUSES,
        format_func=lambda value: value or "All statuses",
    )

    if not st.button("Load support requests"):
        return

    data = run_api_call(
        "Loading support requests…",
        lambda: client.list_support_requests(
            status=optional_text(status),
        ),
    )

    if data is None:
        return

    st.write(f"Total: {data.get('total', 0)}")
    items = data.get("items", [])
    if not items:
        st.write("No support requests found.")
        return

    rows = [
        {
            "id": item.get("id"),
            "status": item.get("status"),
            "requesting": agent_display_name(
                item.get("requesting_agent_code")
            ),
            "supporting": agent_display_name(
                item.get("supporting_agent_code")
            ),
            "provider": provider_label(item.get("provider_code")),
            "type": item.get("transaction_type"),
            "amount": item.get("requested_amount"),
            "created_by": item.get("created_by"),
        }
        for item in items
    ]
    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
        hide_index=True,
    )
    render_technical_detail(data)


def _render_create(client: BackendClient) -> None:
    with st.form("create_support_request_form"):
        requesting = st.selectbox(
            "Requesting agent",
            KNOWN_AGENT_CODES,
            index=KNOWN_AGENT_CODES.index(SAMPLE_AGENT_CODE),
            format_func=agent_display_name,
        )
        supporting = st.selectbox(
            "Supporting agent",
            KNOWN_AGENT_CODES,
            index=KNOWN_AGENT_CODES.index("AGENT-SYL-002"),
            format_func=agent_display_name,
        )
        provider_code = st.selectbox(
            "Provider",
            KNOWN_PROVIDER_CODES,
            format_func=provider_label,
        )
        transaction_type = st.selectbox(
            "Transaction type",
            TRANSACTION_TYPES,
            format_func=lambda value: (
                "Cash in" if value == "cash_in" else "Cash out"
            ),
        )
        requested_amount = st.number_input(
            "Requested amount (৳)",
            min_value=1.0,
            value=1000.0,
            step=100.0,
        )
        reason = st.text_area(
            "Reason",
            value="Temporary float shortfall needs peer support.",
        )
        created_by = st.text_input(
            "Created by",
            value="ops.coordinator",
        )
        operations_owner = st.text_input(
            "Operations owner (optional)",
            value="",
        )
        submitted = st.form_submit_button("Create request")

    if not submitted:
        return

    payload = {
        "requesting_agent_code": requesting,
        "supporting_agent_code": supporting,
        "provider_code": provider_code,
        "transaction_type": transaction_type,
        "requested_amount": requested_amount,
        "reason": reason.strip(),
        "created_by": created_by.strip(),
        "operations_owner": optional_text(operations_owner),
    }

    result = run_api_call(
        "Creating support request…",
        lambda: client.create_support_request(payload),
    )

    if result is None:
        return

    st.success(f"Created support request #{result.get('id')}.")
    st.session_state["selected_support_request"] = result
    st.session_state["support_request_detail_id"] = int(
        result.get("id", 0)
    )


def _render_workflow(client: BackendClient) -> None:
    stored = st.session_state.get("selected_support_request")
    default_id = int(stored.get("id", 0)) if stored else 0

    request_id = st.number_input(
        "Support request id",
        min_value=0,
        step=1,
        value=default_id,
        key="support_request_detail_id",
    )

    if st.button("Load support request"):
        if request_id < 1:
            st.warning("Enter a support request id from the Browse tab.")
            return
        detail = run_api_call(
            "Loading support request…",
            lambda: client.get_support_request(int(request_id)),
        )
        if detail is not None:
            st.session_state["selected_support_request"] = detail

    detail = st.session_state.get("selected_support_request")
    if not detail:
        st.caption(
            "Browse or create a support request, then load it here "
            "to take actions."
        )
        return

    st.subheader(f"Support request #{detail.get('id')}")
    st.write(
        f"**Status:** {detail.get('status')} · "
        f"**Amount:** {detail.get('requested_amount')} · "
        f"**Type:** {detail.get('transaction_type')}"
    )
    st.write(
        f"**From:** {agent_display_name(detail.get('requesting_agent_code'))} → "
        f"**To:** {agent_display_name(detail.get('supporting_agent_code'))} · "
        f"**Provider:** {provider_label(detail.get('provider_code'))}"
    )
    st.write(f"**Reason:** {detail.get('reason')}")

    events = detail.get("events", [])
    if events:
        st.markdown("#### Timeline")
        st.dataframe(events, width="stretch", hide_index=True)

    with st.form("support_workflow_form"):
        actor_code = st.text_input(
            "You are",
            value="ops.coordinator",
        )
        note = st.text_area("Note", value="")
        approved_amount = st.number_input(
            "Approved amount (accept only)",
            min_value=0.0,
            value=float(detail.get("requested_amount") or 0),
            step=100.0,
        )
        action = st.selectbox(
            "Action",
            ["accept", "reject", "escalate", "resolve", "note"],
            format_func=lambda value: value.title(),
        )
        submitted = st.form_submit_button("Submit action")

        if submitted:
            if action == "note" and not note.strip():
                st.error("A note is required for this action.")
            else:
                _apply_support_action(
                    client=client,
                    detail=detail,
                    action=action,
                    actor_code=actor_code.strip(),
                    note=note.strip(),
                    approved_amount=approved_amount,
                )

    render_technical_detail(detail)


def _apply_support_action(
    *,
    client: BackendClient,
    detail: dict,
    action: str,
    actor_code: str,
    note: str,
    approved_amount: float,
) -> None:
    """Apply one support-request workflow action."""

    support_id = int(detail["id"])
    base_payload = {
        "actor_code": actor_code,
        "note": optional_text(note),
    }

    def _call():
        if action == "accept":
            payload = {
                **base_payload,
                "approved_amount": approved_amount,
            }
            return client.accept_support_request(
                support_id,
                payload,
            )
        if action == "reject":
            return client.reject_support_request(
                support_id,
                base_payload,
            )
        if action == "escalate":
            return client.escalate_support_request(
                support_id,
                base_payload,
            )
        if action == "resolve":
            return client.resolve_support_request(
                support_id,
                base_payload,
            )
        return client.add_support_request_note(
            support_id,
            {
                "actor_code": actor_code,
                "actor_role": "operations",
                "note": note.strip(),
            },
        )

    result = run_api_call(f"Applying {action}…", _call)
    if result is not None:
        st.success(f"Support request {action} completed.")
        st.session_state["selected_support_request"] = result
        st.rerun()
