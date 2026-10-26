"""Verify the configured Neon target without printing credentials."""

from __future__ import annotations

import psycopg
from load_neon import database_url


def main() -> int:
    with psycopg.connect(database_url()) as connection:
        database, user, version, research_schema_count = connection.execute(
            """
            select current_database(), current_user,
                   current_setting('server_version'),
                   count(*) from pg_namespace where nspname='research'
            """
        ).fetchone()
    print("connection_ok")
    print(f"database={database}")
    print(f"user={user}")
    print(f"server_version={version}")
    print(f"research_schema_count={research_schema_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
