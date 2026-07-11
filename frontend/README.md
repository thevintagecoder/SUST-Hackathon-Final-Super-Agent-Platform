# Frontend Streamlit Dashboard

Decision-support dashboard for the Super Agent Liquidity and Risk
Intelligence Platform.

## Safety boundary

- Uses synthetic demonstration data only
- Does not connect to PostgreSQL directly
- Does not execute financial actions
- Does not determine or declare fraud

## Install dependencies

From the project root, using the local virtual environment:

```bash
python -m pip install -r frontend/requirements.txt
```

Do not install frontend dependencies into `backend/requirements.txt`.

## Run in mock mode (default)

```bash
python -m streamlit run frontend/app.py
```

Optional environment variables:

```bash
DATA_MODE=mock
API_BASE_URL=http://127.0.0.1:8000
```

## Run in API mode

Use API mode only after the backend dashboard endpoints are available:

```bash
DATA_MODE=api API_BASE_URL=http://127.0.0.1:8000 python -m streamlit run frontend/app.py
```

If API mode fails, the UI shows an explicit error. It does not fall back
to mock data.

## Pages

Navigation is registered explicitly in `frontend/app.py` using
`st.navigation`:

1. Home — unified shared cash + provider balance view
2. Liquidity Forecast — projection chart + plain-language runway panel
3. Anomaly Alerts — unusual-activity flags with expandable evidence
4. Agent Risk Explorer — score breakdown + EN/Bangla narrative
5. Admin Case Management — assign/acknowledge/escalate/resolve + history

## Data architecture

Analytics pages (Home, Liquidity Forecast, Anomaly Alerts, Agent Risk
Explorer) import forecasting, anomaly-detection, risk-scoring, and
narrative logic from the shared `core/` package at the repository root.
`core/` reads the deterministic synthetic dataset in
`synthetic_data/generated/demo/` and contains no Streamlit imports.
Shared sidebar filters (scenario, agent, provider, horizon) live in
`frontend/components/filters.py`.

The Admin Case Management page keeps the data-provider abstraction for
workflow data, using `get_provider()` from `frontend/config.py`.

| Mode | Implementation | Source |
|------|----------------|--------|
| `mock` | `MockDataProvider` | `frontend/mock_data/*.json` |
| `api` | `ApiDataProvider` | FastAPI over HTTP |

## Provisional API contract

These paths are expected from FastAPI in API mode:

| Method | Path |
|--------|------|
| `GET` | `/dashboard/overview` |
| `GET` | `/dashboard/liquidity/{agent_code}` |
| `GET` | `/dashboard/alerts` |
| `GET` | `/dashboard/cases/{case_id}` |
| `POST` | `/dashboard/alerts/{alert_id}/acknowledge` |
| `POST` | `/dashboard/cases/{case_id}/notes` |
| `POST` | `/dashboard/cases/{case_id}/assign` |
| `PATCH` | `/dashboard/cases/{case_id}/status` |

HTTP calls are isolated in `frontend/data/api_provider.py`.

## Run tests

```bash
python -m pytest frontend/tests -v
```
