# Prompt Record 0002 — Configure SQLAlchemy and Alembic

## Date

2026-07-11

## Development goal

Configure SQLAlchemy 2.x and Alembic for the local PostgreSQL database,
create the first minimal Agent model, generate the first migration, and
verify database-schema access.

## AI tool

ChatGPT

## Exact user prompt

> Okay, now I want to move to the work again. Your job is to include the
> instructions and data of the prompt.md again from now on. I ensured the
> connection from FastAPI and PostgreSQL. What do we do next?

## Guidance summary

The next implementation step introduces the ORM and migration layers
without adding API endpoints or multiple domain entities.

The implementation will:

1. configure a SQLAlchemy PostgreSQL engine using existing environment
   settings;
2. create a shared declarative base;
3. create one minimal Agent model;
4. initialize Alembic;
5. connect Alembic to the application's model metadata;
6. generate and review the first database migration;
7. apply the migration to local PostgreSQL;
8. test model behavior using an in-memory SQLite database so GitHub
   Actions does not require a running PostgreSQL server.

## Files affected

Application and model files:

- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/app/models/__init__.py`
- `backend/app/models/agent.py`

Migration files:

- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/README`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/<revision>_create_agents_table.py`

Testing and documentation:

- `backend/requirements.txt`
- `backend/tests/test_agent_model.py`
- `README.md`
- `prompts/0002-configure-sqlalchemy-and-alembic.md`

## Human review and modifications

The implementation uses local PostgreSQL installed through Homebrew.
Docker is not used.

Database credentials continue to load from the ignored `.env` file.
Credentials are not written into the SQLAlchemy model, Alembic files,
GitHub Actions workflow, or prompt record.

Only one real domain table is introduced in this commit.

The generated Alembic migration must be inspected before it is applied.

## Validation required before committing

- verify the active Python interpreter;
- verify PostgreSQL is accepting connections;
- run the complete pytest suite;
- generate the coverage report;
- generate the first Alembic migration;
- inspect the migration operations;
- apply the migration;
- verify that the database revision is at Alembic head;
- verify that the `agents` table exists;
- execute a query through a SQLAlchemy Session;
- retest `GET /health/database`;
- inspect every staged file;
- confirm that `.env` and coverage files remain untracked.

## Post-push validation

- GitHub Actions: pending at commit time;
- SonarQube analysis: pending at commit time;
- Quality Gate: pending at commit time.

GitHub Actions and SonarQube Cloud retain the authoritative results for
the resulting Git commit.
