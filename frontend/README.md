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
`st.navigation`. The sidebar shows:

1. Operations Overview
2. Liquidity
3. Anomaly Review
4. Case Management

## Data-provider abstraction

All pages use `get_provider()` from `frontend/config.py`.

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
| `PATCH` | `/dashboard/cases/{case_id}/status` |

HTTP calls are isolated in `frontend/data/api_provider.py`.

## Run tests

```bash
python -m pytest frontend/tests -v
```
