# Prompt Record 1001 — Build Synthetic Data Generator

## Date

2026-07-11

## Development goal

Create a deterministic, privacy-safe synthetic-data generator for the
Super Agent Liquidity and Risk Intelligence Platform.

The generated data must support liquidity forecasting, provider-specific
shortage detection, anomaly detection, feed-freshness handling, and
measured evaluation against known ground truth.

## AI tool

ChatGPT

## Exact user prompt

> I need to do my teammate's work. Give me the directions for building
> the synthetic-data generator and frontend while keeping the output
> compatible with the backend liquidity models.

## Guidance summary

The first teammate-owned deliverable is a standalone synthetic-data
generator.

The generator:

1. uses a fixed random seed;
2. produces only clearly synthetic identifiers;
3. represents shared physical cash separately;
4. represents BKASH_SIM, NAGAD_SIM, and ROCKET_SIM separately;
5. generates cash-in and cash-out transactions;
6. creates normal and intentionally injected scenarios;
7. stores data-freshness status;
8. stores ground-truth labels and expected shortage information;
9. produces reproducible CSV and JSON files;
10. does not connect directly to FastAPI or PostgreSQL.

The Streamlit frontend will be built only after the generator output is
verified.

## Generated files

- `synthetic_data/generated/demo/initial_positions.csv`
- `synthetic_data/generated/demo/provider_balances.csv`
- `synthetic_data/generated/demo/provider_feed_status.csv`
- `synthetic_data/generated/demo/transactions.csv`
- `synthetic_data/generated/demo/ground_truth.json`

## Source and test files

- `synthetic_data/__init__.py`
- `synthetic_data/scenarios.py`
- `synthetic_data/generator.py`
- `synthetic_data/README.md`
- `synthetic_data/tests/test_generator.py`
- `prompts/1001-build-synthetic-data-generator.md`

## Human review and modifications

All identifiers and financial values are synthetic.

The generator uses the provider codes:

- `BKASH_SIM`
- `NAGAD_SIM`
- `ROCKET_SIM`

A cash-in transaction increases shared physical cash and decreases the
selected provider's electronic balance.

A cash-out transaction decreases shared physical cash and increases the
selected provider's electronic balance.

A transaction for one provider must not directly modify another
provider's electronic balance.

No real personal information, credentials, account numbers, PINs, OTPs,
or financial accounts are used.

## Validation required before committing

- run focused synthetic-data tests;
- generate the bundle twice using the same seed;
- confirm that both outputs are byte-for-byte identical;
- confirm all transaction amounts are positive;
- confirm all providers use approved synthetic identifiers;
- confirm every transaction has a scenario identifier;
- confirm injected anomalies have ground-truth labels;
- confirm the normal scenario is not labelled anomalous;
- inspect all generated files;
- inspect all staged files.

## Future integration

The generated files will later be loaded into PostgreSQL through an
idempotent backend loader.

The Streamlit frontend will communicate with FastAPI through HTTP and
will not read PostgreSQL directly.

## Post-push validation

- GitHub Actions: pending at commit time;
- SonarQube analysis: pending at commit time;
- Quality Gate: pending at commit time.
