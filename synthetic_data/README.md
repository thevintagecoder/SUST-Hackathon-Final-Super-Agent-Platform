# Synthetic Data Generator

This module creates deterministic and privacy-safe demonstration data for
the Super Agent Liquidity and Risk Intelligence Platform.

It does not connect to PostgreSQL, FastAPI, a real provider, or a real
financial account.

## Generate the demonstration bundle

From the project root:

```bash
python -m synthetic_data.generator

Generated files are written to:

synthetic_data/generated/demo/

The bundle contains:

agents.csv
initial_positions.csv
provider_balances.csv
provider_feed_status.csv
transactions.csv
ground_truth.json
```
