# Prompt Record 0005 — Add Core Liquidity Models

## Date

2026-07-11

## Development goal

Create the minimum database schema required to represent shared physical
cash, separate provider electronic balances, synthetic transactions, and
provider-feed freshness.

This schema will support the explainable liquidity-runway forecasting
feature.

## AI tool

ChatGPT

## Exact user prompt

> Okay, I want to start building again now. Give me the steps to build
> the explainable liquidity forecast using recent net flow, runway,
> thresholds, freshness, confidence, and uncertainty.

## Guidance summary

The forecasting calculation requires persisted financial-state and
transaction inputs before analytics can be implemented.

This feature introduces:

1. Provider records;
2. one current shared-cash position for each Agent;
3. one separate electronic balance for each Agent-provider pair;
4. synthetic cash-in and cash-out transactions;
5. provider-feed freshness state;
6. financial and uniqueness constraints;
7. one reviewed Alembic migration;
8. focused model and persistence tests.

Forecast calculations, alerts, stakeholder dashboards, and frontend
integration are intentionally deferred until this schema is verified.

## Files affected

Application models:

- `backend/app/models/provider.py`
- `backend/app/models/agent_position.py`
- `backend/app/models/provider_balance.py`
- `backend/app/models/transaction.py`
- `backend/app/models/__init__.py`

Migration configuration:

- `backend/alembic/env.py`
- `backend/alembic/versions/<revision>_add_core_liquidity_tables.py`

Tests:

- `backend/tests/test_liquidity_models.py`

Prompt tracking:

- `prompts/0005-add-core-liquidity-models.md`

## Human review and modifications

All providers, Agents, customers, balances, and transactions are
synthetic.

Shared physical cash is kept separate from provider electronic balances.

BKASH_SIM, NAGAD_SIM, and ROCKET_SIM balances are not interchangeable.

Money values use decimal-compatible numeric database columns instead of
binary floating-point columns.

A provider balance is uniquely identified by its Agent and provider.

Transaction amounts must be positive.

The generated Alembic migration must be inspected before application.

## Validation required before committing

- verify the active virtual environment;
- verify the current branch is synchronized;
- verify Alembic is at head;
- run focused liquidity-model tests;
- generate and inspect the Alembic migration;
- apply the migration;
- run `alembic current`;
- run `alembic check`;
- inspect PostgreSQL table names and columns;
- run the complete pytest suite with coverage;
- confirm `.env`, `.coverage`, and `coverage.xml` remain ignored;
- inspect every staged file.

## Teammate integration

The teammate's synthetic-data and frontend branches remain separate
during this migration.

The synthetic-data branch will be reviewed and merged only after this
schema is committed and the working tree is clean.

Generated synthetic records will later be loaded into these tables
through an idempotent backend loader.

## Post-push validation

- GitHub Actions: pending at commit time;
- SonarQube analysis: pending at commit time;
- Quality Gate: pending at commit time.

GitHub Actions and SonarQube Cloud retain the authoritative results for
the resulting Git commit.
