# Prompt Record 0021 — Add Alert Human-Review Workflow

## Date

2026-07-11

## Development goal

Add an auditable human-review workflow for persisted multilingual
alerts.

## AI tool

ChatGPT

## Exact user prompt

> What is the next step? Give the instructions.

## Guidance summary

The alert system now supports five human-review actions:

- acknowledge;
- assign;
- add note;
- escalate;
- resolve.

Each action appends an `AlertEvent` instead of silently replacing
history.

The workflow records:

- the human actor;
- optional review notes;
- the previous and new status;
- assignment changes;
- event timestamps.

Resolving an alert sets `human_review_required` to false only after an
explicit human action.

The workflow rejects invalid changes to resolved alerts.

Adding a note preserves the current status and remains available for
audit purposes.

No workflow action moves money, suspends an Agent, or performs an
automatic financial or enforcement action.

## Files affected

- `backend/app/schemas/alert.py`
- `backend/app/services/alert_workflow_service.py`
- `backend/app/routers/alerts.py`
- `backend/tests/test_alert_workflow_api.py`
- `prompts/0021-add-alert-human-review-workflow.md`

## Validation performed

- `python -m compileall backend/app`
- focused alert workflow API tests
- complete alert test group
- complete backend and synthetic-data test suite
- manual Swagger workflow test
- alert detail timeline inspection

## Post-push validation

- GitHub Actions: pending at commit time
- SonarQube: pending at commit time
- Quality Gate: pending at commit time
