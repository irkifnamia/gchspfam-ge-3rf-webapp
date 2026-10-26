from __future__ import annotations

import pyarrow.parquet as pq
import pytest

from scripts.load_neon import ANALYSIS_UNIT_COLUMNS, CANDIDATE_FACT_COLUMNS
from src.config import discover_results_root
from src.constants import EXPECTED_COUNTS
from src.metrics import validate_selected_identities
from src.repository import LocalResultsRepository


@pytest.mark.integration
def test_sibling_validated_results_contract():
    results = discover_results_root()
    if results is None:
        pytest.skip("Validated sibling results project is not available in CI.")
    repository = LocalResultsRepository(results, results.parent / "gchspfam-ge-3rf-webapp")
    counts = repository.dataset_counts()
    for name, expected in EXPECTED_COUNTS.items():
        assert counts[name] == expected
    checks = validate_selected_identities(repository.selected_plans())
    assert checks["risk_sum_error"] <= 5e-12
    assert checks["lp1_error"] <= 5e-12
    assert checks["lp2_error"] <= 5e-12
    assert checks["sample_size_error"] == 0
    assert checks["feasibility_failures"] == 0


@pytest.mark.integration
def test_neon_candidate_loader_covers_authoritative_source_columns():
    results = discover_results_root()
    if results is None:
        pytest.skip("Validated sibling results project is not available in CI.")
    candidate_root = results / "outputs" / "candidates" / "stage6_parquet"
    first_part = sorted(candidate_root.glob("*.parquet"))[0]
    source_columns = set(pq.ParquetFile(first_part).schema_arrow.names)
    loader_columns = set(ANALYSIS_UNIT_COLUMNS) | set(CANDIDATE_FACT_COLUMNS) | {"scenario_id", "prior_id"}
    assert loader_columns == source_columns
