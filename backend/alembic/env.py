"""Alembic migration environment for the application."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from backend.app.core.config import get_settings
from backend.app.db.session import build_database_url
from backend.app.models import Agent


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Agent.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a live connection."""

    database_url = build_database_url(
        get_settings()
    ).render_as_string(
        hide_password=False,
    )

    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live PostgreSQL connection."""

    connectable = create_engine(
        build_database_url(),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()