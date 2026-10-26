"""Independent database-level validation after loading the Neon schema."""

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]


def database_url() -> str:
    value = os.getenv("NEON_DATABASE_URL")
    local_secret = ROOT / ".streamlit" / "admin_secrets.toml"
    if not value and local_secret.is_file():
        payload = tomllib.loads(local_secret.read_text(encoding="utf-8"))
        value = payload.get("database", {}).get("url")
    if not value:
        raise RuntimeError("Set NEON_DATABASE_URL or create the Git-ignored .streamlit/admin_secrets.toml file.")
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


CHECKS = {
    "candidate_records": ("select count(*) from research.candidate_results", 2_592_000),
    "candidate_fact_records": ("select count(*) from research.candidate_fact", 2_592_000),
    "analysis_unit_records": ("select count(*) from research.analysis_units", 5_184),
    "selected_records": ("select count(*) from research.selected_plans", 15_552),
    "matched_records": ("select count(*) from research.matched_framework_results", 5_184),
    "fixed_oc_records": ("select count(*) from research.fixed_plan_oc", 15_552),
    "completed_candidate_partitions": (
        "select count(*) from research.import_manifest where dataset='candidates' and status='complete'",
        48,
    ),
    "candidate_duplicate_keys": (
        "select count(*) from (select scenario_id,prior_id,candidate_g,count(*) from research.candidate_results group by 1,2,3 having count(*)>1) x",
        0,
    ),
    "selected_duplicate_keys": (
        "select count(*) from (select scenario_id,prior_id,framework,count(*) from research.selected_plans group by 1,2,3 having count(*)>1) x",
        0,
    ),
    "selected_feasibility_failures": (
        "select count(*) from research.selected_plans where not feasible or framework_consumer_risk > consumer_risk_limit + 5e-12",
        0,
    ),
    "sample_size_failures": (
        "select count(*) from research.selected_plans where selected_n <> group_size_r * selected_g",
        0,
    ),
    "classical_prior_independence_failures": (
        "select count(*) from (select scenario_id,count(distinct selected_g) n from research.selected_plans where framework='Classical' group by scenario_id having count(distinct selected_g)>1) x",
        0,
    ),
    "design_ratio_invariance_failures": (
        "select count(*) from (select prior_id,termination_multiplier,ge_shape,group_size_r,chain_parameter_i,framework,count(distinct selected_g) n from research.selected_plans group by 1,2,3,4,5,6 having count(distinct selected_g)>1) x",
        0,
    ),
}


def main() -> int:
    results: dict[str, dict[str, int | str]] = {}
    with psycopg.connect(database_url()) as connection:
        for name, (query, expected) in CHECKS.items():
            observed = int(connection.execute(query).fetchone()[0])
            results[name] = {
                "observed": observed,
                "expected": expected,
                "status": "PASS" if observed == expected else "FAIL",
            }

        identity = connection.execute(
            """
            select
                greatest(max(abs(msr-pr-cr)), max(abs(msar-apr-acr)), max(abs(msbr-bpr-bcr))),
                max(abs(l_p1-(1-pr))),
                max(abs(l_p2-cr))
            from research.selected_plans
            """
        ).fetchone()
        for name, value in zip(("risk_sum_max_error", "lp1_max_error", "lp2_max_error"), identity, strict=True):
            observed = float(value)
            results[name] = {"observed": observed, "expected": 0, "status": "PASS" if observed <= 5e-12 else "FAIL"}

        candidate_identity = connection.execute(
            """
            select
                greatest(max(abs(msr-pr-cr)), max(abs(msar-apr-acr)), max(abs(msbr-bpr-bcr))),
                max(abs(l_p1-(1-pr))),
                max(abs(l_p2-cr)),
                max(abs(candidate_n-group_size_r*candidate_g))
            from research.candidate_results
            """
        ).fetchone()
        for name, value in zip(
            (
                "candidate_risk_sum_max_error",
                "candidate_lp1_max_error",
                "candidate_lp2_max_error",
                "candidate_sample_size_max_error",
            ),
            candidate_identity,
            strict=True,
        ):
            observed = float(value)
            results[name] = {
                "observed": observed,
                "expected": 0,
                "status": "PASS" if observed <= 5e-12 else "FAIL",
            }

        minimality_failures = int(
            connection.execute(
                """
                with first_feasible as (
                    select scenario_id,prior_id,'Classical' framework,min(candidate_g) selected_g
                    from research.candidate_results where classical_feasible group by 1,2
                    union all
                    select scenario_id,prior_id,'Average',min(candidate_g)
                    from research.candidate_results where average_feasible group by 1,2
                    union all
                    select scenario_id,prior_id,'Bayesian',min(candidate_g)
                    from research.candidate_results where bayesian_feasible group by 1,2
                )
                select count(*) from research.selected_plans s
                join first_feasible f using (scenario_id,prior_id,framework)
                where s.selected_g <> f.selected_g
                """
            ).fetchone()[0]
        )
        results["selected_minimality_failures"] = {
            "observed": minimality_failures,
            "expected": 0,
            "status": "PASS" if minimality_failures == 0 else "FAIL",
        }

        size_rows = connection.execute(
            """
            select relname, pg_total_relation_size(oid)
            from pg_class
            where relnamespace = 'research'::regnamespace and relkind in ('r', 'i')
            order by pg_total_relation_size(oid) desc
            """
        ).fetchall()
        database_size = int(connection.execute("select pg_database_size(current_database())").fetchone()[0])

    overall = "PASS" if all(row["status"] == "PASS" for row in results.values()) else "FAIL"
    print(
        json.dumps(
            {
                "overall_status": overall,
                "checks": results,
                "storage": {
                    "database_bytes": database_size,
                    "research_relations": {name: int(size) for name, size in size_rows},
                },
            },
            indent=2,
        )
    )
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
