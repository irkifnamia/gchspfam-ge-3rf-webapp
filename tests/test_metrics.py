from __future__ import annotations

from src.metrics import framework_overview, validate_selected_identities


def test_framework_overview_preserves_framework_order(selected_frame):
    summary = framework_overview(selected_frame)
    assert summary.framework.tolist() == ["Classical", "Average", "Bayesian"]
    assert summary.mean_selected_g.tolist() == [3.0, 2.0, 1.0]


def test_selected_identities(selected_frame):
    checks = validate_selected_identities(selected_frame)
    assert checks["risk_sum_error"] < 1e-15
    assert checks["lp1_error"] < 1e-15
    assert checks["lp2_error"] == 0
    assert checks["sample_size_error"] == 0
    assert checks["feasibility_failures"] == 0
