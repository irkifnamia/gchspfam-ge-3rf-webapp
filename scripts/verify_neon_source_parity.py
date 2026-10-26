"""Compare imported Neon values with authoritative local research outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import psycopg
import pyarrow.dataset as ds
from load_neon import database_url

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_G_SAMPLE = (1, 2, 250, 499, 500)


def query_frame(connection: psycopg.Connection[Any], query: str) -> pd.DataFrame:
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [item.name for item in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=columns)


def compare_frames(
    authoritative: pd.DataFrame,
    imported: pd.DataFrame,
    keys: list[str],
) -> dict[str, Any]:
    authoritative = authoritative.sort_values(keys, kind="stable").reset_index(drop=True)
    imported = imported.sort_values(keys, kind="stable").reset_index(drop=True)
    if authoritative.columns.tolist() != imported.columns.tolist():
        raise ValueError("Source and Neon columns differ")
    if len(authoritative) != len(imported):
        raise ValueError(f"Source has {len(authoritative):,} rows; Neon has {len(imported):,}")

    mismatch_count = 0
    maximum_absolute_error = 0.0
    differing_columns: list[str] = []
    for column in authoritative.columns:
        left = authoritative[column]
        right = imported[column]
        if pd.api.types.is_numeric_dtype(left.dtype) and not pd.api.types.is_bool_dtype(left.dtype):
            left_values = left.to_numpy(dtype=float)
            right_values = right.to_numpy(dtype=float)
            equal = (left_values == right_values) | (np.isnan(left_values) & np.isnan(right_values))
            errors = np.abs(left_values - right_values)
            if errors.size and not np.isnan(errors).all():
                maximum_absolute_error = max(maximum_absolute_error, float(np.nanmax(errors)))
        else:
            equal = left.astype("string").fillna("<NA>").to_numpy() == right.astype("string").fillna("<NA>").to_numpy()
        different = int((~equal).sum())
        if different:
            mismatch_count += different
            differing_columns.append(column)

    return {
        "rows": len(authoritative),
        "columns": len(authoritative.columns),
        "cell_mismatches": mismatch_count,
        "differing_columns": differing_columns,
        "maximum_absolute_error": maximum_absolute_error,
        "status": "PASS" if mismatch_count == 0 else "FAIL",
    }


def main() -> int:
    results_root = ROOT.parent / "gchspfam-ge-3rf-results"
    candidate_root = results_root / "outputs" / "candidates" / "stage6_parquet"
    analytics_root = results_root / "outputs" / "analytics"

    candidate_dataset = ds.dataset(candidate_root, format="parquet")
    candidate_source = candidate_dataset.to_table(filter=ds.field("candidate_g").isin(CANDIDATE_G_SAMPLE)).to_pandas()
    selected_source = pd.read_parquet(analytics_root / "selected_plans_research_ready.parquet")
    matched_source = pd.read_parquet(analytics_root / "matched_framework_results.parquet")
    fixed_source = pd.read_csv(
        results_root / "outputs" / "stage9" / "data" / "fixed_plan_oc_evaluations.csv",
        float_precision="round_trip",
    )

    with psycopg.connect(database_url()) as connection:
        sampled = ",".join(map(str, CANDIDATE_G_SAMPLE))
        candidate_imported = query_frame(
            connection,
            f"select * from research.candidate_results where candidate_g in ({sampled})",
        )
        selected_imported = query_frame(connection, "select * from research.selected_plans")
        matched_imported = query_frame(connection, "select * from research.matched_framework_results")
        fixed_imported = query_frame(connection, "select * from research.fixed_plan_oc")

    results = {
        "candidate_deterministic_sample": compare_frames(
            candidate_source,
            candidate_imported,
            ["scenario_id", "prior_id", "candidate_g"],
        ),
        "selected_plans_full": compare_frames(
            selected_source,
            selected_imported,
            ["scenario_id", "prior_id", "framework"],
        ),
        "matched_results_full": compare_frames(
            matched_source,
            matched_imported,
            ["scenario_id", "prior_id"],
        ),
        "fixed_oc_full": compare_frames(
            fixed_source,
            fixed_imported,
            ["fixed_plan_id", "evaluation_mean_life_ratio"],
        ),
    }
    overall = "PASS" if all(item["status"] == "PASS" for item in results.values()) else "FAIL"
    print(json.dumps({"overall_status": overall, "comparisons": results}, indent=2))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
