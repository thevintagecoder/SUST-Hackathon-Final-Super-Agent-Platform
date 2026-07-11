# Super Agent Liquidity & Risk Intelligence Platform

A hackathon prototype for simulated multi-provider liquidity monitoring,
unusual-activity review, and human operational coordination.

## Safety boundary

This project:

- uses synthetic data only;
- does not connect to real wallets or financial accounts;
- does not execute financial transactions;
- does not determine or declare fraud;
- requires human review for risk-related decisions.

## Current development status

Completed:

- FastAPI application
- `GET /health`
- Swagger UI and ReDoc
- automated API tests
- environment-based configuration
- `.env.example`

Not added yet:

- PostgreSQL
- transaction data
- liquidity analytics
- anomaly detection
- Streamlit

## Local configuration

Create the local configuration file:

```bash
cp .env.example .env
```

The local `.env` file is ignored by Git.

## Run the backend

From the project root:

```bash
source .venv/bin/activate
python -m uvicorn backend.app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## Run tests

```bash
python -m pytest backend/tests -q
```
