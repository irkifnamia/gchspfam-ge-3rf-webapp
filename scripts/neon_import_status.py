"""Report resumable Neon import progress without exposing credentials."""

from __future__ import annotations

import psycopg
from load_neon import database_url


def main() -> int:
    with psycopg.connect(database_url()) as connection:
        completed, candidate_rows, database_bytes = connection.execute(
            """
            select
                (select count(*) from research.import_manifest
                 where dataset='candidates' and status='complete'),
                (select count(*) from research.candidate_fact),
                pg_database_size(current_database())
            """
        ).fetchone()
    print(f"completed_partitions={int(completed)}/48")
    print(f"candidate_rows={int(candidate_rows):,}/2,592,000")
    print(f"database_mib={int(database_bytes) / 1024**2:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
