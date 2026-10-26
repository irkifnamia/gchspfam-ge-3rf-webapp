"""Load the validated research outputs into Neon PostgreSQL.

Candidate partitions are committed independently and tracked by SHA-256 in
``research.import_manifest`` so an interrupted 2.59-million-row import can be
resumed without duplicating already verified partitions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg
import pyarrow.parquet as pq
from psycopg import sql
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import discover_results_root  # noqa: E402

EXPECTED = {"candidates": 2_592_000, "selected": 15_552, "matched": 5_184, "fixed_oc": 15_552}

ANALYSIS_UNIT_COLUMNS = [
    "scenario_id",
    "prior_id",
    "prior_mean",
    "prior_sd",
    "beta_alpha",
    "beta_beta",
    "acceptable_mean_life_ratio",
    "termination_multiplier",
    "ge_shape",
    "group_size_r",
    "chain_parameter_i",
    "p1",
    "p2",
    "prior_good_probability",
    "prior_bad_probability",
]

CANDIDATE_FACT_COLUMNS = [
    "candidate_g",
    "candidate_n",
    "pr",
    "apr",
    "bpr",
    "cr",
    "acr",
    "bcr",
    "msr",
    "msar",
    "msbr",
    "l_p1",
    "l_p2",
    "classical_feasible",
    "average_feasible",
    "bayesian_feasible",
]


def database_url() -> str:
    value = os.getenv("NEON_DATABASE_URL")
    local_secret = ROOT / ".streamlit" / "admin_secrets.toml"
    if not value and local_secret.is_file():
        payload = tomllib.loads(local_secret.read_text(encoding="utf-8"))
        value = payload.get("database", {}).get("url")
    if not value:
        raise RuntimeError("Set NEON_DATABASE_URL or create the Git-ignored .streamlit/admin_secrets.toml file.")
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def python_value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value.item() if hasattr(value, "item") else value


def copy_rows(
    connection: psycopg.Connection[Any],
    table: str,
    columns: list[str],
    rows: Iterable[tuple[Any, ...]],
) -> int:
    statement = sql.SQL("COPY {}.{} ({}) FROM STDIN").format(
        sql.Identifier("research"),
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
    )
    count = 0
    with connection.cursor() as cursor, cursor.copy(statement) as copy:
        for row in rows:
            copy.write_row(tuple(python_value(value) for value in row))
            count += 1
    return count


def mark_manifest(
    connection: psycopg.Connection[Any],
    dataset: str,
    source_file: str,
    digest: str,
    source_rows: int,
    imported_rows: int,
    status: str,
) -> None:
    connection.execute(
        """
        insert into research.import_manifest
            (dataset, source_file, sha256, source_rows, imported_rows, status, imported_at)
        values (%s, %s, %s, %s, %s, %s, now())
        on conflict (dataset, source_file) do update set
            sha256=excluded.sha256,
            source_rows=excluded.source_rows,
            imported_rows=excluded.imported_rows,
            status=excluded.status,
            imported_at=excluded.imported_at
        """,
        (dataset, source_file, digest, source_rows, imported_rows, status),
    )


def manifest_complete(
    connection: psycopg.Connection[Any], dataset: str, source_file: str, digest: str, rows: int
) -> bool:
    result = connection.execute(
        """
        select status='complete' and sha256=%s and source_rows=%s and imported_rows=%s
        from research.import_manifest where dataset=%s and source_file=%s
        """,
        (digest, rows, rows, dataset, source_file),
    ).fetchone()
    return bool(result and result[0])


def replace_frame(
    connection: psycopg.Connection[Any], dataset: str, table: str, path: Path, frame: pd.DataFrame
) -> None:
    digest = file_sha256(path)
    source_rows = len(frame)
    with connection.transaction():
        connection.execute(sql.SQL("TRUNCATE TABLE research.{}").format(sql.Identifier(table)))
        imported = copy_rows(connection, table, list(frame.columns), frame.itertuples(index=False, name=None))
        mark_manifest(connection, dataset, path.name, digest, source_rows, imported, "complete")
    print(f"{dataset}: imported {imported:,} rows from {path.name}")


def sync_analysis_units(connection: psycopg.Connection[Any], parts: list[Path]) -> dict[tuple[str, str], int]:
    """Load each candidate unit's invariant metadata exactly once."""
    frames = [pq.read_table(path, columns=ANALYSIS_UNIT_COLUMNS).to_pandas().drop_duplicates() for path in parts]
    units = pd.concat(frames, ignore_index=True).drop_duplicates()
    duplicated_keys = units.duplicated(["scenario_id", "prior_id"], keep=False)
    if duplicated_keys.any():
        examples = units.loc[duplicated_keys, ["scenario_id", "prior_id"]].head().to_dict("records")
        raise ValueError(f"Conflicting invariant candidate metadata for analysis units: {examples}")
    if len(units) != EXPECTED["matched"]:
        raise ValueError(f"Expected {EXPECTED['matched']:,} analysis units, found {len(units):,}")

    assignments = ",\n                ".join(f"{column}=excluded.{column}" for column in ANALYSIS_UNIT_COLUMNS[2:])
    statement = f"""
        insert into research.analysis_units ({", ".join(ANALYSIS_UNIT_COLUMNS)})
        values ({", ".join(["%s"] * len(ANALYSIS_UNIT_COLUMNS))})
        on conflict (scenario_id, prior_id) do update set
                {assignments}
    """
    rows = [tuple(python_value(value) for value in row) for row in units.itertuples(index=False, name=None)]
    with connection.transaction(), connection.cursor() as cursor:
        cursor.executemany(statement, rows)

    mapping = {
        (str(scenario_id), str(prior_id)): int(unit_id)
        for unit_id, scenario_id, prior_id in connection.execute(
            "select analysis_unit_id, scenario_id, prior_id from research.analysis_units"
        ).fetchall()
    }
    missing = set(zip(units.scenario_id.astype(str), units.prior_id.astype(str), strict=True)) - set(mapping)
    if missing:
        raise ValueError(f"Analysis-unit identifiers were not created for {len(missing)} keys")
    print(f"analysis_units: synchronized {len(units):,} prior-scenario combinations")
    return mapping


def import_candidates(connection: psycopg.Connection[Any], results_root: Path) -> None:
    candidate_root = results_root / "outputs" / "candidates" / "stage6_parquet"
    parts = sorted(candidate_root.glob("*.parquet"))
    if len(parts) != 48:
        raise ValueError(f"Expected 48 candidate partitions, found {len(parts)}")
    unit_ids = sync_analysis_units(connection, parts)
    imported_total = 0
    for position, path in enumerate(parts, start=1):
        parquet = pq.ParquetFile(path)
        source_rows = parquet.metadata.num_rows
        digest = file_sha256(path)
        if manifest_complete(connection, "candidates", path.name, digest, source_rows):
            stored = connection.execute(
                "select count(*) from research.candidate_fact where source_part=%s", (path.name,)
            ).fetchone()[0]
            if stored == source_rows:
                print(f"candidates [{position:02d}/48]: {path.name} already complete ({stored:,} rows)")
                imported_total += stored
                continue
        try:
            with connection.transaction():
                connection.execute("delete from research.candidate_fact where source_part=%s", (path.name,))
                mark_manifest(connection, "candidates", path.name, digest, source_rows, 0, "running")
                imported = 0
                for batch in parquet.iter_batches(batch_size=10_000):
                    frame = batch.to_pandas()
                    identifiers = [
                        unit_ids[(str(scenario_id), str(prior_id))]
                        for scenario_id, prior_id in zip(frame.scenario_id, frame.prior_id, strict=True)
                    ]
                    fact = frame[CANDIDATE_FACT_COLUMNS]
                    rows = (
                        (unit_id, *tuple(row), path.name)
                        for unit_id, row in zip(
                            identifiers,
                            fact.itertuples(index=False, name=None),
                            strict=True,
                        )
                    )
                    imported += copy_rows(
                        connection,
                        "candidate_fact",
                        ["analysis_unit_id", *CANDIDATE_FACT_COLUMNS, "source_part"],
                        rows,
                    )
                if imported != source_rows:
                    raise ValueError(f"{path.name}: imported {imported}, expected {source_rows}")
                mark_manifest(connection, "candidates", path.name, digest, source_rows, imported, "complete")
            imported_total += imported
            print(f"candidates [{position:02d}/48]: imported {imported:,} rows from {path.name}")
        except Exception:
            with connection.transaction():
                mark_manifest(connection, "candidates", path.name, digest, source_rows, 0, "failed")
            raise
    if imported_total != EXPECTED["candidates"]:
        raise ValueError(f"Candidate import total {imported_total:,} != {EXPECTED['candidates']:,}")


def import_selected(connection: psycopg.Connection[Any], results_root: Path) -> None:
    path = results_root / "outputs" / "analytics" / "selected_plans_research_ready.parquet"
    replace_frame(connection, "selected", "selected_plans", path, pd.read_parquet(path))


def import_matched(connection: psycopg.Connection[Any], results_root: Path) -> None:
    path = results_root / "outputs" / "analytics" / "matched_framework_results.parquet"
    replace_frame(connection, "matched", "matched_framework_results", path, pd.read_parquet(path))


def import_fixed_oc(connection: psycopg.Connection[Any], results_root: Path) -> None:
    path = results_root / "outputs" / "stage9" / "data" / "fixed_plan_oc_evaluations.csv"
    frame = pd.read_csv(path, float_precision="round_trip")
    replace_frame(connection, "fixed_oc", "fixed_plan_oc", path, frame)


def import_validation(connection: psycopg.Connection[Any], results_root: Path) -> None:
    path = results_root / "outputs" / "stage10" / "verification" / "final_validation_summary.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    with connection.transaction():
        connection.execute(
            """
            insert into research.validation_summary (name, payload, imported_at)
            values ('stage10_final', %s, now())
            on conflict (name) do update set payload=excluded.payload, imported_at=excluded.imported_at
            """,
            (Jsonb(payload),),
        )
    print("validation: imported Stage 10 summary")


def apply_schema(connection: psycopg.Connection[Any]) -> None:
    schema = (ROOT / "db" / "schema.sql").read_text(encoding="utf-8")
    with connection.transaction():
        connection.execute(schema)
    print("schema: applied successfully")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path)
    parser.add_argument("--apply-schema", action="store_true")
    parser.add_argument("--selected", action="store_true")
    parser.add_argument("--matched", action="store_true")
    parser.add_argument("--fixed-oc", action="store_true")
    parser.add_argument("--candidates", action="store_true")
    parser.add_argument("--validation", action="store_true")
    parser.add_argument("--all", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results_root = args.results_dir or discover_results_root()
    if results_root is None:
        raise RuntimeError("Results project was not found; use --results-dir or GCHSPFAM_RESULTS_DIR.")
    results_root = results_root.resolve()
    # Autocommit keeps read checks outside an implicit long-running transaction;
    # each explicit transaction below is therefore a durable resume checkpoint.
    with psycopg.connect(database_url(), autocommit=True) as connection:
        if args.apply_schema or args.all:
            apply_schema(connection)
        if args.selected or args.all:
            import_selected(connection, results_root)
        if args.matched or args.all:
            import_matched(connection, results_root)
        if args.fixed_oc or args.all:
            import_fixed_oc(connection, results_root)
        if args.validation or args.all:
            import_validation(connection, results_root)
        if args.candidates or args.all:
            import_candidates(connection, results_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
