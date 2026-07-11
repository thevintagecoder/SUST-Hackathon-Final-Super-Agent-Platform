# Prompt Record 1102 — Build Dashboard Pages and Core Analytics

## Date

2026-07-11

## Development goal

Adapt the existing Streamlit frontend to the dashboard-page specification
while introducing a shared `core/` analytics package at the repository
root. Dashboard pages must import forecasting, anomaly detection, risk
scoring, and narrative logic from `core/` rather than reimplementing it.
Preserve the mock/API provider abstraction for Admin Case Management.

## AI tool

Cursor

## Exact user prompt

> save this progress and create new branch or fork whatev its called for me
> to work on so that if its good ill push later. if this requires the
> already made backend or frontend to dramatically change, ask me for
> approval after explaining what different is implementing. here i want to
> work on: --
> name: dashboard-page
> description: Use when building or editing a Streamlit page under
> dashboard/ — unified balance view, liquidity forecast charts,
> anomaly/alert lists, agent risk explorer, admin case management, or map
> view.
> ---
>
> # Dashboard Page Skill
>
> ## Rules for every page
> - Import from `core/` only — never reimplement forecasting/anomaly/risk
>   logic inside a dashboard file.
> - Use Plotly for charts ...
> - Every anomaly/alert display must show: the evidence (which
>   transactions), the confidence/severity, and the recommended next step
> ...
> - Handle the empty/missing-data case explicitly ...
> - Keep filters (agent/provider/area/time) in a sidebar ...
>
> ## Page-specific notes
> - `Home.py`: combined cash + 3 provider balances ...
> - `1_Liquidity_Forecast.py`: forecast line chart + plain-language panel
> - `2_Anomaly_Alerts.py`: list of flags, click-to-expand evidence
> - `3_Agent_Risk_Explorer.py`: risk score breakdown + EN/Bangla toggle
> - `4_Admin_Case_Management.py`: alert table with assign/acknowledge/
>   escalate/resolve actions, and case history/log per alert
> - `5_Map_View.py`: Nice to Have only

Follow-up (approach approval):

> Adapt into existing frontend/ (Recommended) ...
> Standalone core/ package at repo root (Recommended) ...

Follow-up (push and documentation):

> push in git with prompt under prompt folder w suitable file name for
> Frontend update like the rest as documentation is imp. make sure .yml is
> also updated as need for sonarqube

## Guidance summary

The implementation:

1. created branch `feature/dashboard-pages` from `feature/frontend`;
2. added `core/` with `data_access`, `forecast`, `anomaly`, `risk`, and
   `narrative` (English and Bangla) modules backed by
   `synthetic_data/generated/demo/`;
3. renamed and reworked Streamlit pages to match the spec:
   - `Home.py` — unified shared cash + provider balances with status
     badges;
   - `1_Liquidity_Forecast.py` — observed/projected Plotly line chart
     and plain-language runway panel;
   - `2_Anomaly_Alerts.py` — expandable flags with transaction evidence;
   - `3_Agent_Risk_Explorer.py` — new component breakdown page with
     EN/বাংলা narrative toggle;
   - `4_Admin_Case_Management.py` — alert queue, assign/acknowledge/
     escalate/resolve actions, append-only case history;
4. added shared sidebar filters in `frontend/components/filters.py`;
5. extended the data-provider protocol with `assign_case()` for mock and
   API modes;
6. added `core/tests/test_core_analytics.py` and
   `frontend/tests/test_pages_smoke.py`;
7. updated GitHub Actions and SonarQube configuration to analyze and
   cover `core/` and `frontend/`;
8. skipped `5_Map_View.py` (Nice to Have per spec).

Analytics pages compute from `core/` + synthetic CSVs. Admin Case
Management continues to use mock JSON via `get_provider()`.

## Files affected

Core analytics:

- `core/__init__.py`
- `core/data_access.py`
- `core/forecast.py`
- `core/anomaly.py`
- `core/risk.py`
- `core/narrative.py`
- `core/tests/__init__.py`
- `core/tests/test_core_analytics.py`

Frontend dashboard:

- `frontend/app.py`
- `frontend/README.md`
- `frontend/components/filters.py`
- `frontend/data/provider.py`
- `frontend/data/mock_provider.py`
- `frontend/data/api_provider.py`
- `frontend/pages/Home.py`
- `frontend/pages/1_Liquidity_Forecast.py`
- `frontend/pages/2_Anomaly_Alerts.py`
- `frontend/pages/3_Agent_Risk_Explorer.py`
- `frontend/pages/4_Admin_Case_Management.py`
- `frontend/tests/test_contracts.py`
- `frontend/tests/test_pages_smoke.py`

CI and quality:

- `.github/workflows/quality.yml`
- `.coveragerc`
- `sonar-project.properties`
- `prompts/1102-build-dashboard-pages-and-core-analytics.md`

Removed (renamed via git mv in prior commit):

- `frontend/pages/1_Operations_Overview.py`
- `frontend/pages/2_Liquidity.py`
- `frontend/pages/3_Anomaly_Review.py`
- `frontend/pages/4_Case_Management.py`

## Human review and modifications

All dashboard values remain synthetic demonstration data.

The user approved adapting the existing `frontend/` layout rather than
creating a parallel `dashboard/` app or replacing the provider
abstraction entirely.

Shared physical cash is displayed separately from provider electronic
balances. Alert and risk language remains decision-support only — no
fraud declarations or automatic blocks.

`5_Map_View.py` was intentionally deferred.

`backend/requirements.txt` was not modified.

## Validation performed

- `python -m pytest core/tests frontend/tests synthetic_data/tests -q`
  — 21 passed;
- `python -m pytest frontend/tests/test_pages_smoke.py -q` — 10 passed;
- `python -m streamlit run frontend/app.py` — app served HTTP 200;
- all five pages render without exception across demo scenarios;
- EN/বাংলা narrative toggle verified on Agent Risk Explorer;
- assign/acknowledge/escalate/resolve actions update mock case timeline.

## SonarQube result

- GitHub Actions: pending at commit time;
- SonarQube analysis: pending at commit time;
- Quality Gate: pending at commit time.

The authoritative post-push results will be retained by GitHub Actions and
SonarQube Cloud and associated with the resulting Git commit.
