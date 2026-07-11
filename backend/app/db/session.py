"""SQLAlchemy engine and request-scoped session configuration."""

from collections.abc import Generator

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import Settings, get_settings


def build_database_url(
    settings: Settings | None = None,
) -> URL:
    """Build the PostgreSQL connection URL from settings."""

    active_settings = settings or get_settings()

    return URL.create(
        drivername="postgresql+psycopg",
        username=active_settings.database_user,
        password=(
            active_settings.database_password.get_secret_value()
        ),
        host=active_settings.database_host,
        port=active_settings.database_port,
        database=active_settings.database_name,
    )


engine: Engine = create_engine(
    build_database_url(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Provide one SQLAlchemy Session for one API request."""

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()