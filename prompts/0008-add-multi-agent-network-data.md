# Prompt Record 0008 — Add Multi-Agent Network Data

## Date

2026-07-11

## Development goal

Extend the platform from one synthetic Agent to a small network of
Agents that can support customer referral and human-approved liquidity
coordination.

## AI tool

ChatGPT

## Exact user prompts

> Done with Phase 2. Start the next step, which is extending synthetic
> data to multiple Agents.

> I pasted the requested command outputs. Give me the next steps.

> Give me the steps to add `agents.csv`, create four synthetic Agents,
> and introduce the `NETWORK-001` scenario.

## Guidance summary

This feature is implemented incrementally.

The first increment adds optional latitude and longitude fields to the
existing Agent model. These coordinates will later allow the platform to
calculate approximate distance between a requesting Agent and potential
supporting Agents.

Later increments will:

1. generate four clearly synthetic Agents;
2. create a `NETWORK-001` scenario;
3. give each Agent different physical-cash and provider balances;
4. mark one apparently capable Agent's data as delayed;
5. update the synthetic loader to load multiple Agents;
6. preserve loader idempotence;
7. prepare the data for the Agent-to-Agent matching endpoint.

Coordinates remain optional so existing database rows are not broken by
the migration.

The synthetic generator now produces `agents.csv` containing four
clearly synthetic located Agents.

The new `NETWORK-001` scenario represents:

- AGENT-SYL-001 with insufficient Nagad electronic float;
- AGENT-SYL-002 with fresh excess Nagad capacity;
- AGENT-SYL-003 with high physical-cash capacity;
- AGENT-SYL-004 with high reported Nagad capacity but delayed data.

The scenario ground truth includes a simulated ৳80,000 Nagad cash-in
request at AGENT-SYL-001, an expected local shortfall of ৳60,000, the
preferred fresh candidate, and the stale candidate.

The existing loader is not yet used for NETWORK-001 because it currently
expects one Agent per scenario. Multi-Agent loader support is deferred to
the next increment.

## Files affected in this increment

- `backend/app/models/agent.py`
- `backend/alembic/versions/<revision>_add_agent_coordinates.py`
- `backend/tests/test_agent_location_model.py`
- `prompts/0008-add-multi-agent-network-data.md`
- `synthetic_data/scenarios.py`
- `synthetic_data/generator.py`
- `synthetic_data/tests/test_generator.py`
- `synthetic_data/README.md`
- `synthetic_data/generated/demo/agents.csv`

## Human review and modifications

All locations belong to clearly synthetic demonstration Agents.

Coordinates are used only for approximate demonstration ranking.

The platform does not track real Agents or customer locations.

Location information does not authorize a transfer or guarantee that
another Agent can provide support.

## Validation

- run the focused Agent-location model test;
- generate and inspect the Alembic migration;
- apply the migration;
- verify Alembic is at head;
- verify the new PostgreSQL columns;
- run the complete existing test suite;
- inspect staged changes before committing.

## Post-push validation

- GitHub Actions: pending at commit time;
- SonarQube: pending at commit time;
- Quality Gate: pending at commit time.
