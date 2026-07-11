# Prompt Record 0019 — Add Persisted Alert Generation

## Date

2026-07-11

## Development goal

Generate and persist multilingual alerts from existing liquidity,
anomaly, freshness, and serviceability intelligence.

## AI tool

ChatGPT

## Exact user prompt

> Increment 3 passed, give the instructions for increment 4.

## Guidance summary

The alert-generation service connects the persistent alert models to
four existing risk and liquidity signals:

- liquidity runway forecasts;
- explainable anomaly detection;
- delayed or uncertain provider-balance data;
- immediate transaction serviceability shortfalls.

The service creates an alert only when the relevant condition is
detected.

Every stored alert contains:

- English, Bangla, and Banglish text;
- severity;
- structured evidence;
- confidence;
- freshness information;
- a human-review requirement;
- a `CREATED` timeline event;
- confirmation that no automatic action was taken.

A deterministic deduplication key prevents the same evidence from
creating repeated alert rows.

Liquidity alerts are created only for `HIGH` or `CRITICAL` runway risk.

Anomaly alerts use unusual-activity wording and do not declare confirmed
fraud.

Serviceability shortfalls identify the exact required resource:

- provider-specific electronic float for cash-in;
- shared physical cash for cash-out.

## Files affected

- `backend/app/schemas/alert.py`
- `backend/app/services/alert_generation_service.py`
- `backend/tests/test_alert_generation_service.py`
- `prompts/0019-add-persisted-alert-generation.md`

## Validation performed

- `python -m compileall backend/app`
- `python -m pytest backend/tests/test_alert_generation_service.py -v`
- `python -m pytest backend/tests/test_alert_templates.py backend/tests/test_alert_models.py backend/tests/test_alert_generation_service.py -v`
- `python -m pytest backend/tests synthetic_data/tests -q`
- PostgreSQL alert-generation and deduplication checks

## Safety

The generation service creates reviewable warnings only.

It does not:

- automatically move money;
- automatically reserve another Agent's resources;
- suspend or penalize an Agent;
- claim that an anomaly is confirmed fraud;
- guarantee that a forecast shortage will occur.

## Post-push validation

- GitHub Actions: pending at commit time
- SonarQube: pending at commit time
- Quality Gate: pending at commit time
