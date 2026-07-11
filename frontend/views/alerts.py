"""Human-readable alert inbox and review workflow."""

from __future__ import annotations

import streamlit as st

from frontend.api.client import BackendClient
from frontend.components.common import (
    ALERT_STATUSES,
    ALERT_TYPES,
    KNOWN_AGENT_CODES,
    KNOWN_PROVIDER_CODES,
    SAMPLE_SCENARIO_ID,
    active_language,
    agent_display_name,
    alert_status_label,
    alert_type_label,
    localized_text,
    navigate_to_peer_support,
    optional_text,
    provider_label,
    render_alert_card,
    render_empty_state,
    render_evidence_summary,
    render_summary_metrics,
    render_technical_detail,
    run_api_call,
    safety_notice,
    severity_label,
)


def _refresh_alerts(client: BackendClient) -> dict | None:
    """Fetch alerts using the current inbox filters."""

    status = st.session_state.get("alert_filter_status", "All active")
    status_value = None if status == "All active" else status
    result = run_api_call(
        "Refreshing alert inbox…",
        lambda: client.list_alerts(
            status=status_value,
            agent_code=optional_text(
                st.session_state.get(
                    "alert_filter_agent",
                    "",
                )
            ),
            provider_code=optional_text(
                st.session_state.get(
                    "alert_filter_provider",
                    "",
                )
            ),
            scenario_id=st.session_state.get("scenario_id"),
            limit=50,
        ),
    )
    if result is not None and status == "All active":
        result["items"] = [
            item
            for item in result.get("items", [])
            if item.get("status") != "RESOLVED"
        ]
    return result


def render_alerts(client: BackendClient) -> None:
    """Render the alert inbox, evidence, ownership, and actions."""

    st.header("Alert inbox")
    st.markdown(
        '<div class="section-intro">'
        "Each alert is a work item for a risk that happened or may "
        "happen soon. Read who is affected, who owns the review, "
        "and what to do next — then acknowledge, assign, or resolve."
        "</div>",
        unsafe_allow_html=True,
    )
    safety_notice()

    inbox_tab, checks_tab = st.tabs(
        ["Review alerts", "Run a risk check"]
    )
    with inbox_tab:
        _render_inbox(client)
    with checks_tab:
        _render_risk_check(client)


def _render_inbox(client: BackendClient) -> None:
    """Render filters, inbox list, and selected detail."""

    filters = st.columns([1, 1.3, 1.3])
    with filters[0]:
        st.selectbox(
            "Status",
            ["All active"] + ALERT_STATUSES[1:],
            format_func=lambda value: (
                "All active"
                if value == "All active"
                else alert_status_label(value)
            ),
            key="alert_filter_status",
        )
    with filters[1]:
        st.selectbox(
            "Affected agent",
            [""] + KNOWN_AGENT_CODES,
            format_func=lambda value: (
                agent_display_name(value) if value else "All agents"
            ),
            key="alert_filter_agent",
        )
    with filters[2]:
        st.selectbox(
            "Provider",
            [""] + KNOWN_PROVIDER_CODES,
            format_func=lambda value: (
                provider_label(value) if value else "All providers"
            ),
            key="alert_filter_provider",
        )

    data = _refresh_alerts(client)
    if data is None:
        return

    alerts = data.get("items", [])
    if not alerts:
        render_empty_state(
            "No risk alerts yet",
            "Run a customer check on Customer service or a risk check "
            "here to create one when evidence supports it.",
        )
        return

    inbox, detail_column = st.columns([1, 1.35], gap="large")
    alert_ids = [int(alert["id"]) for alert in alerts]
    if st.session_state.get("selected_alert_id") not in alert_ids:
        st.session_state["selected_alert_id"] = alert_ids[0]

    with inbox:
        st.caption(f"{len(alerts)} work item(s)")
        for alert in alerts:
            render_alert_card(alert)

        if len(alerts) > 1:
            st.selectbox(
                "Switch alert",
                alert_ids,
                format_func=lambda alert_id: f"Alert #{alert_id}",
                key="selected_alert_id",
            )

    with detail_column:
        selected_id = int(st.session_state["selected_alert_id"])
        detail = run_api_call(
            "Opening alert…",
            lambda: client.get_alert(int(selected_id)),
        )
        if detail is not None:
            _render_alert_detail(client, detail)


def _render_alert_detail(
    client: BackendClient,
    detail: dict,
) -> None:
    """Render one complete alert and its review actions."""

    language = active_language()
    title = (
        localized_text(detail.get("title"), language=language)
        or alert_type_label(detail.get("alert_type"))
    )
    st.subheader(title)
    st.caption(
        f"Alert #{detail.get('id')} · "
        f"{alert_type_label(detail.get('alert_type'))}"
    )

    render_summary_metrics(
        [
            ("Priority", severity_label(detail.get("severity"))),
            ("Status", alert_status_label(detail.get("status"))),
            (
                "Affected agent",
                agent_display_name(detail.get("agent_code")) or "—",
            ),
            ("Owner", detail.get("assigned_to") or "Unassigned"),
        ]
    )

    st.markdown("#### Why this alert was prompted")
    message = localized_text(detail.get("message"), language=language)
    if message:
        st.write(message)
    else:
        st.caption("No explanation text was returned.")

    st.markdown("#### Recommended next step")
    next_step = localized_text(detail.get("next_step"), language=language)
    if next_step:
        st.info(next_step)
    else:
        st.caption("No next step text was returned.")

    if (
        detail.get("alert_type") == "SERVICEABILITY_SHORTFALL"
        and detail.get("status") != "RESOLVED"
    ):
        st.caption(
            "Ops is notified — rescue the customer by finding peer support."
        )
        if st.button(
            "Find peer support",
            type="primary",
            key=f"peer_support_{detail['id']}",
        ):
            navigate_to_peer_support(detail)
            st.rerun()

    evidence, history = st.columns(2)
    with evidence:
        st.markdown("#### Supporting evidence")
        render_evidence_summary(detail.get("evidence", {}))
        render_technical_detail(detail.get("evidence", {}))
    with history:
        st.markdown("#### Review history")
        events = detail.get("events", [])
        if events:
            for event in events:
                st.write(
                    f"**{event.get('event_type', 'update').replace('_', ' ').title()}** · "
                    f"{event.get('actor', 'system')}"
                )
                if event.get("note"):
                    st.caption(event["note"])
        else:
            st.caption("No human action recorded yet.")

    if detail.get("status") == "RESOLVED":
        st.success("This alert is resolved.")
        with st.expander("Audit history is still available"):
            st.caption(
                "Resolved alerts are removed from active risk counts "
                "but remain visible through the Resolved filter."
            )
        return

    with st.expander("Take ownership or update this alert", expanded=True):
        with st.form(f"alert_action_{detail['id']}"):
            actor = st.text_input(
                "You are",
                value="operations.reviewer",
            )
            assigned_to = st.text_input(
                "Owner",
                value=detail.get("assigned_to")
                or "operations.reviewer",
            )
            note = st.text_area(
                "Review note",
                placeholder=(
                    "What did you verify, decide, or hand over?"
                ),
            )
            action = st.selectbox(
                "Action",
                [
                    "Acknowledge",
                    "Assign owner",
                    "Add note",
                    "Escalate",
                    "Resolve",
                ],
            )
            submitted = st.form_submit_button(
                "Update alert",
                type="primary",
            )

            if submitted:
                _apply_alert_action(
                    client=client,
                    detail=detail,
                    action=action,
                    actor=actor.strip(),
                    assigned_to=assigned_to.strip(),
                    note=note.strip(),
                )


def _apply_alert_action(
    *,
    client: BackendClient,
    detail: dict,
    action: str,
    actor: str,
    assigned_to: str,
    note: str,
) -> None:
    """Apply one human-review transition."""

    alert_id = int(detail["id"])
    if not actor:
        st.error("Actor is required.")
        return
    if action == "Assign owner" and not assigned_to:
        st.error("Assigned owner is required.")
        return
    actor_payload = {
        "actor": actor,
        "note": optional_text(note),
    }

    if action == "Acknowledge":
        call = lambda: client.acknowledge_alert(
            alert_id,
            actor_payload,
        )
    elif action == "Assign owner":
        call = lambda: client.assign_alert(
            alert_id,
            {
                **actor_payload,
                "assigned_to": assigned_to,
            },
        )
    elif action == "Add note":
        if not note:
            st.error("A note is required for this action.")
            return
        call = lambda: client.add_alert_note(
            alert_id,
            {"actor": actor, "note": note},
        )
    elif action == "Escalate":
        call = lambda: client.escalate_alert(
            alert_id,
            actor_payload,
        )
    else:
        call = lambda: client.resolve_alert(
            alert_id,
            actor_payload,
        )

    result = run_api_call("Updating alert…", call)
    if result is not None:
        st.success(f"Alert updated: {action.lower()}.")
        st.rerun()


def _render_risk_check(client: BackendClient) -> None:
    """Run a backend evaluator that can persist a real alert."""

    st.write(
        "Risk checks evaluate current backend data. An alert is created "
        "only when the selected condition is actually detected."
    )

    with st.form("risk_check_form"):
        alert_type = st.selectbox(
            "Risk to evaluate",
            [value for value in ALERT_TYPES if value],
            format_func=alert_type_label,
        )
        agent_code = st.selectbox(
            "Affected agent",
            KNOWN_AGENT_CODES,
            format_func=agent_display_name,
        )
        provider_code = st.selectbox(
            "Provider",
            KNOWN_PROVIDER_CODES,
            format_func=provider_label,
        )
        transaction_type = st.selectbox(
            "Customer request",
            ["cash_in", "cash_out"],
            format_func=lambda value: (
                "Cash-in (uses provider float)"
                if value == "cash_in"
                else "Cash-out (uses shared cash)"
            ),
        )
        requested_amount = st.number_input(
            "Customer amount",
            min_value=1.0,
            value=50000.0,
            step=1000.0,
        )
        submitted = st.form_submit_button(
            "Run check",
            type="primary",
        )

    if not submitted:
        return

    payload = {
        "alert_type": alert_type,
        "agent_code": agent_code,
        "provider_code": provider_code,
        "scenario_id": st.session_state.get("scenario_id"),
    }
    if alert_type == "SERVICEABILITY_SHORTFALL":
        payload.update(
            {
                "transaction_type": transaction_type,
                "requested_amount": requested_amount,
            }
        )

    result = run_api_call(
        "Evaluating current data…",
        lambda: client.generate_alert(payload),
    )
    if result is None:
        return

    if result.get("alert_created"):
        st.success(
            "Condition detected. Alert "
            f"#{result.get('alert_id')} was prompted for human review. "
            "Open the Review alerts tab to read it in your selected "
            "language."
        )
    elif result.get("deduplicated"):
        st.info(
            "This condition is already represented by alert "
            f"#{result.get('alert_id')}; no duplicate was created."
        )
    else:
        st.success(
            "Check completed. No alert was needed: "
            f"{result.get('reason')}"
        )
