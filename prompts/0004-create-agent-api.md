# Prompt Record 0004 — Create Agent API

## Date

2026-07-11

## Development goal

Create the first database-backed Agent API endpoint using FastAPI,
Pydantic, SQLAlchemy, and the existing PostgreSQL agents table.

## AI tool

ChatGPT

## Exact user prompt

> Okay, what is the next step now? Alembic work is done.

## Guidance summary

The implementation introduces one small vertical feature:

1. validate an Agent creation request with Pydantic;
2. provide one SQLAlchemy Session per API request;
3. place Agent creation logic in a service module;
4. expose `POST /agents`;
5. return HTTP 201 for successful creation;
6. return HTTP 409 for a duplicate agent code;
7. return HTTP 422 for invalid request data;
8. test the endpoint using an isolated in-memory SQLite database.

No Provider, balance, transaction, alert, or frontend functionality is
added in this commit.

## Files affected

Application files:

- `backend/app/db/session.py`
- `backend/app/main.py`
- `backend/app/routers/__init__.py`
- `backend/app/routers/agents.py`
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/agent.py`
- `backend/app/services/__init__.py`
- `backend/app/services/agent_service.py`

Testing:

- `backend/tests/test_agents_api.py`
- `backend/tests/test_database_session.py`

Prompt tracking:

- `prompts/0004-create-agent-api.md`

## Human review and modifications

The endpoint creates only synthetic agent records.

The API does not connect to real financial accounts and does not perform
financial actions.

Database credentials remain loaded from the ignored `.env` file.

The duplicate-code rule is checked in the service layer and is also
protected by the database unique constraint.

Tests override the real database-session dependency with an isolated
SQLite session. The tests do not modify the local PostgreSQL database.

## Validation required before committing

- verify the active Python interpreter;
- verify the Alembic revision is at head;
- run focused Agent API tests;
- run the complete pytest suite;
- generate coverage.xml;
- start FastAPI;
- create one Agent through Swagger UI;
- test a duplicate Agent code;
- test an invalid request;
- verify the created row in PostgreSQL;
- inspect all staged files;
- confirm `.env` and coverage files remain untracked.

## Post-push validation

- GitHub Actions: pending at commit time;
- SonarQube analysis: pending at commit time;
- Quality Gate: pending at commit time.

GitHub Actions and SonarQube Cloud retain the authoritative results for
the resulting Git commit.
