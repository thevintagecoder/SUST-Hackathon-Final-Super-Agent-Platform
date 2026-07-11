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

Phase 1, Step 1:

- FastAPI application
- `GET /health`
- Swagger UI
- automated health tests

## Run the backend

From the project root:

```bash
source .venv/bin/activate
python -m uvicorn backend.app.main:app --reload
```
