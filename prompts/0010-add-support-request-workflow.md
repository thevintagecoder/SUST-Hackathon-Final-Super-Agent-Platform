# Prompt Record 0010 — Add Support Request Workflow

## Date

2026-07-11

## Development goal

Persist the human coordination workflow that follows Agent-to-Agent
liquidity discovery.

## AI tool

ChatGPT

## Exact user prompt

> Build the part where a support request is created, the supporting Agent
> accepts or rejects it, Operations monitors it, the request is resolved
> or escalated, and the complete timeline is stored.

## Guidance summary

This feature adds two database models:

1. `SupportRequest`;
2. `SupportRequestEvent`.

A support request records:

- requesting Agent;
- proposed supporting Agent;
- provider;
- transaction type;
- required resource;
- requested amount;
- approved amount;
- status;
- reason;
- creator;
- Operations owner;
- timestamps.

The workflow supports:

- creation in pending state;
- acceptance by the supporting Agent;
- rejection by the supporting Agent;
- escalation by Operations;
- resolution by Operations;
- append-only timeline notes;
- Operations queue filtering by status.

Every status transition creates a new timeline event containing the actor,
actor role, previous state, new state, note, and timestamp.

The feature does not transfer, reserve, settle, or convert money.

## Files affected

- `backend/app/models/support_request.py`
- `backend/app/models/support_request_event.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/support_request.py`
- `backend/app/services/support_request_service.py`
- `backend/app/routers/support_requests.py`
- `backend/app/main.py`
- `backend/alembic/versions/<revision>_add_support_request_workflow.py`
- `backend/tests/test_support_request_api.py`
- `prompts/0010-add-support-request-workflow.md`

## Validation

- create a pending request;
- verify a created event is stored;
- accept all or part of a request;
- reject a pending request;
- escalate a pending or accepted request;
- resolve an accepted or escalated request;
- add a note without changing status;
- list requests for Operations;
- reject invalid workflow transitions;
- verify the complete timeline;
- run all tests;
- generate coverage;
- inspect the migration;
- inspect staged files.

## Safety

The workflow records coordination decisions only.

It does not:

- automatically move money;
- reserve another Agent's balance;
- guarantee candidate availability;
- perform provider settlement;
- collect customer credentials;
- automatically approve a transaction.
