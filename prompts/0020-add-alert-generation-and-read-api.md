# Prompt Record 0020 — Add Alert Generation and Read API

## Date

2026-07-11

## Development goal

Expose persisted multilingual alert generation, listing, filtering,
and detail retrieval through FastAPI endpoints.

## AI tool

ChatGPT

## Exact user prompt

> Give the steps for Increment 5.

## Guidance summary

The persistent alert system is exposed through three endpoints:

- `POST /alerts/generate`;
- `GET /alerts`;
- `GET /alerts/{alert_id}`.

The generation endpoint evaluates existing explainable evidence and
persists an alert only when the relevant condition is detected.

The list endpoint supports filtering by:

- alert status;
- alert type;
- Agent;
- provider;
- synthetic scenario.

It also supports limit-and-offset pagination.

The detail endpoint returns:

- English, Bangla, and Banglish titles;
- English, Bangla, and Banglish messages;
- localized recommended next steps;
- structured evidence;
- confidence and freshness;
- assignment and workflow timestamps;
- the alert event timeline.

FastAPI response models define the frontend contract.

The alert timeline is eagerly loaded for the detail endpoint.

The endpoints do not perform financial or enforcement actions.

## Files affected

- `backend/app/schemas/alert.py`
- `backend/app/services/alert_service.py`
- `backend/app/routers/alerts.py`
- `backend/app/main.py`
- `backend/tests/test_alert_api.py`
- `prompts/0020-add-alert-generation-and-read-api.md`

## Validation performed

- `python -m compileall backend/app`
- `python -m pytest backend/tests/test_alert_api.py -v`
- all alert tests
- complete backend and synthetic-data test suite
- manual Swagger test of alert generation
- manual Swagger test of alert listing and filtering
- manual Swagger test of alert detail and timeline retrieval

## Safety

The endpoints expose reviewable warnings only.

They do not:

- automatically move money;
- reserve another Agent's resources;
- suspend or penalize an Agent;
- declare an anomaly to be confirmed fraud;
- guarantee that a predicted shortage will occur.

## Post-push validation

- GitHub Actions: pending at commit time
- SonarQube: pending at commit time
- Quality Gate: pending at commit time
