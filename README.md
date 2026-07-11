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

Completed:

- FastAPI application
- `GET /health`
- Swagger UI and ReDoc
- automated API tests
- environment-based configuration
- `.env.example`

Not added yet:

- PostgreSQL
- transaction data
- liquidity analytics
- anomaly detection
- Streamlit

## Local configuration

Create the local configuration file:

```bash
cp .env.example .env
```

The local `.env` file is ignored by Git.

## Run the backend

From the project root:

```bash
source .venv/bin/activate
python -m uvicorn backend.app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## Run tests

```bash
python -m pytest backend/tests -q
```

## Local PostgreSQL

PostgreSQL runs directly on macOS through Homebrew. Docker is not
required for local development.

Locate the PostgreSQL commands:

```bash
PG_BIN="$(brew --prefix postgresql@17)/bin"
```

Start PostgreSQL:

```bash
brew services start postgresql@17
```

Check its status:

```bash
brew services list
```

Check whether it accepts connections:

```bash
"$PG_BIN/pg_isready"
```

Verify the real Python connection:

```bash
python -m backend.app.db.connection
```

Stop PostgreSQL:

```bash
brew services stop postgresql@17
```

Restart PostgreSQL:

```bash
brew services start postgresql@17
```

## SQLAlchemy and Alembic

The application uses SQLAlchemy 2.x for ORM-based database access and
Alembic for reproducible database-schema migrations.

### Apply all migrations

From the project root:

```bash
python -m alembic -c backend/alembic.ini upgrade head
```

### View the current migration

```bash
python -m alembic -c backend/alembic.ini current
```

### Check for model changes without a migration

```bash
python -m alembic -c backend/alembic.ini check
```

### Create a migration after changing a model

```bash
python -m alembic \
  -c backend/alembic.ini \
  revision \
  --autogenerate \
  -m "describe the schema change"
```

Generated migrations must be reviewed before they are applied.

### Current database tables

- `alembic_version`
- `agents`
