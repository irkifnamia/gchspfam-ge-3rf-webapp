from __future__ import annotations

import json

import pandas as pd

from src.repository import NeonResultsRepository, _normalise_database_url


def test_local_repository_filters_selected_plans(local_repository):
    result = local_repository.selected_plans({"framework": ["Bayesian"]})
    assert len(result) == 1
    assert result.iloc[0].selected_g == 1


def test_local_repository_candidate_trace(local_repository):
    trace = local_repository.candidate_trace("S001", "B1")
    assert trace.candidate_g.tolist() == [1, 2]
    assert len(trace) == 2


def test_database_url_uses_psycopg_driver():
    assert _normalise_database_url("postgresql://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"


def test_neon_repository_reuses_packaged_analytics_and_returns_copies(tmp_path, selected_frame):
    analytics = tmp_path / "data" / "analytics"
    analytics.mkdir(parents=True)
    selected_frame.to_parquet(analytics / "selected_plans_research_ready.parquet", index=False)
    selected_frame.iloc[[0]].to_parquet(analytics / "matched_framework_results.parquet", index=False)
    selected_frame.iloc[[0]].to_parquet(analytics / "fixed_plan_oc_evaluations.parquet", index=False)

    repository = NeonResultsRepository("postgresql://user:pass@localhost/test", tmp_path)
    repository._query = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected query"))

    assert repository.uses_packaged_analytics
    first = repository.selected_plans()
    first.loc[0, "selected_g"] = 999
    second = repository.selected_plans()
    assert second.loc[0, "selected_g"] != 999


def test_neon_candidate_trace_caches_recent_queries_and_returns_copies(tmp_path):
    repository = NeonResultsRepository("postgresql://user:pass@localhost/test", tmp_path)
    calls = 0

    def fake_query(_sql, _parameters=None):
        nonlocal calls
        calls += 1
        return pd.DataFrame({"candidate_g": [1, 2], "cr": [0.2, 0.08]})

    repository._query = fake_query
    first = repository.candidate_trace("S001", "B1")
    first.loc[0, "cr"] = 999
    second = repository.candidate_trace("S001", "B1")
    assert calls == 1
    assert second.loc[0, "cr"] == 0.2


def test_neon_counts_use_validated_deployment_metadata_without_query(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    payload = {
        "database": {
            "candidate_records": 2_592_000,
            "selected_records": 15_552,
            "matched_records": 5_184,
            "candidate_partitions": 48,
        }
    }
    (data / "neon_deployment_validation.json").write_text(json.dumps(payload), encoding="utf-8")
    repository = NeonResultsRepository("postgresql://user:pass@localhost/test", tmp_path)
    repository._query = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected query"))

    counts = repository.dataset_counts()
    assert counts["candidate_records"] == 2_592_000
    assert counts["selected_records"] == 15_552
    assert counts["matched_records"] == 5_184
