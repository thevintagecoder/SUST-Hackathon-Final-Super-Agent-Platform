# Prompt Record 0018 — Add Alert Tables Migration

## Date

2026-07-11

## Development goal

Create, review, apply, reverse, and reapply the PostgreSQL migration
for persistent multilingual alerts and their human-review timelines.

## AI tool

ChatGPT

## Exact user prompt

> Okay, now give me the steps for increment 3 again.

## Guidance summary

An Alembic migration was generated from the tested `Alert` and
`AlertEvent` SQLAlchemy models.

The migration creates:

- the `alerts` table;
- the `alert_events` table;
- foreign keys to Agents and providers;
- the alert-to-event cascade relationship;
- alert type, severity, status, and confidence constraints;
- a unique alert deduplication key;
- indexes for alert workflow and scenario queries.

The migration was validated by:

- compiling the migration file;
- applying it to PostgreSQL;
- confirming both tables exist;
- downgrading one revision;
- reapplying the migration;
- confirming the database is at Alembic head;
- running `alembic check`;
- running focused and complete automated tests.

All Alembic commands use:

```text
alembic -c backend/alembic.ini
```
