# Prompt Record 0016 — Add Multilingual Alert Templates

## Date

2026-07-11

## Development goal

Add responsible alert templates in English, Bangla, and Banglish
before introducing alert persistence and workflow endpoints.

## AI tool

ChatGPT

## Exact user prompt

> Okay, get started with the alert system.

## Guidance summary

The first alert-system increment provides localized templates for:

- liquidity runway warnings;
- unusual transaction patterns;
- delayed provider data;
- serviceability shortfalls.

Each template returns:

- an English version using the `en` key;
- a Bangla version using the `bn` key;
- a Banglish version using the `bn_latn` key;
- a title;
- an explanatory message;
- a safe recommended next step.

Dynamic evidence such as provider name, forecast runway, resource name,
and shortfall amount is inserted into the appropriate template.

Bangla alert values use Bangla digits where appropriate.

The wording does not declare fraud, blame an Agent, guarantee a future
shortage, or initiate an automatic financial action.

## Files affected

- `backend/app/schemas/alert.py`
- `backend/app/services/alert_templates.py`
- `backend/tests/test_alert_templates.py`
- `prompts/0016-add-multilingual-alert-templates.md`

## Validation performed

- `python -m pytest backend/tests/test_alert_templates.py -v`
- `python -m pytest backend/tests synthetic_data/tests -q`

## Post-push validation

- GitHub Actions: pending at commit time
- SonarQube: pending at commit time
- Quality Gate: pending at commit time
