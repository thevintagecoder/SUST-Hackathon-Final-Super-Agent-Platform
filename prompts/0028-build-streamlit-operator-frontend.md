# Prompt Record 0028 — Build Streamlit Operator Frontend

## Date

2026-07-12

## Development goal

Complete the Streamlit frontend as an operator-facing Ops Center that
connects to the existing FastAPI backend without modifying backend code.
The UI must support Agent liquidity review, provider network views,
operations triage, alert human-review workflow, customer serviceability
checks, multilingual alert text, and demo scenario selection.

## AI tool

Cursor (Composer)

## Exact user prompt

> backend api is done. help me finish up the frontend and connect them.
> without errors that occur with frontend connection with backend. read all
> api points created.
>
> make the frontend make sense for the goal of the project but make it more
> usable. interpretable. nice to look at for agents dealing with bkash nagad
> providers and their customers. i hate the sidebar so change that into a
> different format. and if theres any discrepency with the data not loading
> fix that. and give me test cases to run and check. keep necessary endpoints
> and connect them. and for dashboard and to show stats wherever necessary use
> pandas numpy. alerts should make sense that an alert was prompted. u r like
> a senior frontend engineer and im like the intern who made the backend
> stand and know why this backend is important. there should be shown shared
> cash reserve and separate balances for each provider. show important alert,
> who receives it, who owns it , recommended next step. use backend for help
>
> dont break backend code as it is more important than frontend
>
> this version was good i want to save it so commit it push to branch in
> shared repo called frontend. also generate the .md for prompt used following
> format in prompts folder

## Guidance summary

The frontend remains a Streamlit presentation layer only. All data is
retrieved through a centralized `BackendClient` (`httpx`) against the
completed FastAPI API. No SQLAlchemy, PostgreSQL, or backend service code
is accessed directly from the UI.

The implementation adds:

- a full HTTP client covering health, dashboards, alerts, liquidity,
  network support, forecasts, anomalies, and support-request endpoints;
- an Ops Center shell with bottom navigation (Dashboard, Liquidity,
  Anomalies, Cases) and advanced stakeholder pages;
- shared UI components for money formatting, provider labels, freshness
  states, localized alert text, scenario metadata, and branded styling;
- Agent desk with separate shared physical cash and per-provider float
  cards (bKash, Nagad, Rocket);
- Provider and Operations dashboards with pandas/NumPy summaries;
- alert inbox with recipient, owner, evidence, next step, and human-review
  workflow actions (acknowledge, assign, note, escalate, resolve);
- customer serviceability and risk-check flows that can prompt persisted
  alerts through `POST /alerts/generate`;
- scenario and language controls in the header context bar;
- frontend automated tests and a manual testing checklist.

Backend source files were intentionally left unchanged.

## Files affected

- `.env.example`
- `README.md`
- `frontend/api/client.py`
- `frontend/app.py`
- `frontend/requirements.txt`
- `frontend/TESTING.md`
- `frontend/components/__init__.py`
- `frontend/components/common.py`
- `frontend/components/scenarios.py`
- `frontend/components/styles.py`
- `frontend/tests/test_api_client.py`
- `frontend/tests/test_ui_helpers.py`
- `frontend/views/__init__.py`
- `frontend/views/overview.py`
- `frontend/views/agent_dashboard.py`
- `frontend/views/provider_dashboard.py`
- `frontend/views/operations_dashboard.py`
- `frontend/views/alerts.py`
- `frontend/views/support_requests.py`
- `frontend/views/tools.py`
- `frontend/views/cases.py`
- `frontend/views/evaluation_dashboard.py`
- `prompts/0028-build-streamlit-operator-frontend.md`

## Human review and modifications

The developer reviewed the Ops Center layout, bottom navigation, scenario
selector, alert workflow, and bKash/Nagad-focused balance cards. Backend
code was not modified. The saved version keeps frontend-only changes and
documents that alert and workflow data persist in each developer's local
PostgreSQL rather than in Git.

## Validation performed

- `python -m pytest frontend/tests -q` — 12 passed
- `python -m compileall -q frontend` — passed
- Streamlit `AppTest` smoke test across main navigation pages — no
  exceptions
- Manual backend health check: `GET /health` and `GET /health/database`
- Manual alert workflow check: serviceability shortfall →
  `POST /alerts/generate` → alert detail with recipient, owner, and next
  step
- Confirmed `git status --short -- backend` shows no backend source
  changes

## SonarQube result

Pending — to be recorded after this commit is pushed and analyzed.

Example:

- GitHub Actions: pending
- Quality Gate: pending
- Commit: pending
