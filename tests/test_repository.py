from __future__ import annotations

from src.repository import _normalise_database_url


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
