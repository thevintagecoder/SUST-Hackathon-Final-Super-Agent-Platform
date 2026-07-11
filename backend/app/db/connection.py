"""Low-level PostgreSQL connectivity checks."""

import psycopg

from backend.app.core.config import Settings, get_settings


def check_database_connection(
    settings: Settings | None = None,
) -> bool:
    """Connect to PostgreSQL and execute a minimal test query."""

    active_settings = settings or get_settings()

    with psycopg.connect(
        host=active_settings.database_host,
        port=active_settings.database_port,
        dbname=active_settings.database_name,
        user=active_settings.database_user,
        password=(
            active_settings.database_password.get_secret_value()
        ),
        connect_timeout=(
            active_settings.database_connect_timeout_seconds
        ),
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()

    return result == (1,)


def main() -> None:
    """Run the connectivity check directly from the terminal."""

    try:
        connected = check_database_connection()
    except psycopg.Error as exc:
        print(
            "Database connection failed: "
            f"{exc.__class__.__name__}"
        )
        raise SystemExit(1) from exc

    if not connected:
        print(
            "Database connection failed: "
            "unexpected SELECT 1 result."
        )
        raise SystemExit(1)

    print(
        "Database connection successful: "
        "SELECT 1 returned 1."
    )


if __name__ == "__main__":
    main()