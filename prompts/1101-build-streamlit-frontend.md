# Prompt Record 1101 — Build Streamlit Frontend

## Date

2026-07-11

## Development goal

Create a mock-first, four-page Streamlit dashboard for the Super Agent
Liquidity and Risk Intelligence Platform.

The frontend must use a data-provider abstraction so the same UI works
with local mock JSON now and FastAPI later, without accessing PostgreSQL
directly from Streamlit.

## AI tool

Cursor

## Exact user prompt

> Streamlit Frontend Implementation Plan
>
> Implement the plan as specified, it is attached for your reference.
> Do NOT edit the plan file itself.

## Guidance summary

The implementation introduces:

1. a separate `frontend/` package with its own dependencies;
2. `DATA_MODE=mock` by default and `DATA_MODE=api` for integrated demos;
3. a `DataProvider` interface with mock and API implementations;
4. four handbook-aligned mock JSON contracts;
5. shared UI components for badges, metrics, alerts, and timelines;
6. four multipage Streamlit views for operations, liquidity, anomaly
   review, and case management;
7. provisional FastAPI dashboard paths isolated in `api_provider.py`;
8. focused contract tests for mock payloads and provider behavior.

## Generated files

- `frontend/app.py`
- `frontend/config.py`
- `frontend/requirements.txt`
- `frontend/README.md`
- `frontend/components/badges.py`
- `frontend/components/metric_cards.py`
- `frontend/components/alert_card.py`
- `frontend/components/timeline.py`
- `frontend/data/contracts.py`
- `frontend/data/provider.py`
- `frontend/data/mock_provider.py`
- `frontend/data/api_provider.py`
- `frontend/mock_data/overview.json`
- `frontend/mock_data/liquidity.json`
- `frontend/mock_data/alerts.json`
- `frontend/mock_data/case.json`
- `frontend/pages/1_Operations_Overview.py`
- `frontend/pages/2_Liquidity.py`
- `frontend/pages/3_Anomaly_Review.py`
- `frontend/pages/4_Case_Management.py`
- `frontend/tests/test_contracts.py`
- `prompts/1101-build-streamlit-frontend.md`

## Human review and modifications

All dashboard values are synthetic.

Shared physical cash is displayed separately from provider electronic
balances.

The UI uses responsible decision-support language and does not present
automatic blocks, accusations, or money-transfer controls.

API mode surfaces backend errors explicitly and does not silently fall
back to mock data.

`backend/requirements.txt` was not modified.

## Validation required before committing

- install `frontend/requirements.txt` in the local `.venv`;
- run `python -m pytest frontend/tests -v`;
- run `python -m streamlit run frontend/app.py` in mock mode;
- open all four pages without exceptions;
- confirm the synthetic-data banner is visible;
- confirm provider balances remain separate;
- confirm freshness, confidence, evidence, and uncertainty are visible;
- confirm no forbidden fraud language appears;
- inspect all staged files;
- stage only `frontend/**` and this prompt record.

## Future integration

Switch to `DATA_MODE=api` after the backend teammate implements the
provisional `/dashboard/*` endpoints with the same response shapes as the
mock JSON contracts.

## Post-push validation

- GitHub Actions: pending at commit time;
- SonarQube analysis: pending at commit time;
- Quality Gate: pending at commit time.
