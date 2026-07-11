# Prompt Record 0006 — Integrate and Load Synthetic Data

## Date

2026-07-11

## Development goal

Connect the deterministic synthetic-data generator to the PostgreSQL
liquidity schema through a validated and idempotent backend loader.

## AI tool

ChatGPT

## Exact user prompt

> I finished the synthetic-data generator. What is the next step?

## Guidance summary

The generated CSV and JSON files currently exist outside the database.

This feature introduces a backend loader that:

1. selects one demonstration scenario;
2. validates the required generated files;
3. creates or reuses the synthetic Agent;
4. creates or reuses the three synthetic providers;
5. creates or updates the Agent's current shared-cash position;
6. creates or updates each provider-specific electronic balance;
7. inserts the selected scenario's transactions;
8. skips transactions that were already loaded;
9. commits only after successful validation;
10. rolls back the database transaction when loading fails.

The current liquidity tables represent current state rather than
scenario-specific snapshots. Therefore, one scenario is activated at a
time. Loading another scenario updates current balances while preserving
previously loaded transaction history.

## Files affected

Application files:

- `backend/app/data_loading/__init__.py`
- `backend/app/data_loading/synthetic_loader.py`

Tests:

- `backend/tests/test_synthetic_loader.py`

Quality configuration:

- `.github/workflows/quality.yml`
- `sonar-project.properties`

Prompt tracking:

- `prompts/0006-integrate-and-load-synthetic-data.md`

## Human review and modifications

Only clearly synthetic Agents, providers, customers, balances, and
transactions are loaded.

The loader does not use real provider accounts or customer data.

Transaction amounts are parsed as Decimal values.

The loader is idempotent: running the same scenario twice does not
duplicate transactions.

The frontend will not read CSV files or PostgreSQL directly. It will later
receive analyzed information through FastAPI HTTP endpoints.

## Validation required before committing

- verify the generator tests pass;
- verify the liquidity-model tests pass;
- load `REPEATED-001` into an isolated test database;
- run the same load twice;
- verify the second load inserts zero duplicate transactions;
- load the scenario into local PostgreSQL;
- verify the Agent, providers, balances, and transactions;
- run the loader a second time against PostgreSQL;
- confirm transaction counts remain unchanged;
- run all backend and synthetic-data tests;
- generate coverage.xml;
- inspect every staged file;
- confirm `.env`, `.coverage`, and `coverage.xml` remain ignored.

## Post-push validation

- GitHub Actions: pending at commit time;
- SonarQube analysis: pending at commit time;
- Quality Gate: pending at commit time.

GitHub Actions and SonarQube Cloud retain the authoritative results for
the resulting Git commit.
