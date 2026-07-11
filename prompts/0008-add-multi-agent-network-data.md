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

## Files affected in this increment

- `backend/app/models/agent.py`
- `backend/alembic/versions/<revision>_add_agent_coordinates.py`
- `backend/tests/test_agent_location_model.py`
- `prompts/0008-add-multi-agent-network-data.md`

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
