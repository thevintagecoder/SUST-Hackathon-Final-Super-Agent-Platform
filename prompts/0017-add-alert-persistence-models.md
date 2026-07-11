# Prompt Record 0017 — Add Alert Persistence Models

## Date

2026-07-11

## Development goal

Add persistent database models for multilingual alerts and their
human-review timelines.

## AI tool

ChatGPT

## Exact user prompt

> Done with this part, give the next steps.

## Guidance summary

The alert persistence increment introduces two SQLAlchemy models:

- `Alert`, which stores multilingual alert content, evidence, confidence,
  freshness, severity, workflow status, assignment, and timestamps;
- `AlertEvent`, which stores the append-only action timeline for each
  alert.

Each stored alert contains English, Bangla, and Banglish versions of:

- the alert title;
- the explanatory message;
- the recommended next step.

The alert also stores structured evidence separately from translated
presentation text.

A unique deduplication key is included so later alert-generation logic
can avoid repeatedly creating the same open warning.

The timeline supports future events such as:

- creation;
- acknowledgement;
- assignment;
- note;
- escalation;
- resolution.

The models preserve the safety properties that human review is explicit
and no automatic financial action is recorded.

## Files affected

- `backend/app/models/alert.py`
- `backend/app/models/alert_event.py`
- `backend/app/models/__init__.py`
- `backend/tests/test_alert_models.py`
- `prompts/0017-add-alert-persistence-models.md`

## Validation performed

- `python -m pytest backend/tests/test_alert_models.py -v`
- `python -m pytest backend/tests/test_alert_templates.py backend/tests/test_alert_models.py -v`
- model import check

## Post-push validation

- GitHub Actions: pending at commit time
- SonarQube: pending at commit time
- Quality Gate: pending at commit time
