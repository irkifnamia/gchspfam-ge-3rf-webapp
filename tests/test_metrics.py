from __future__ import annotations

import pandas as pd

from src.metrics import (
    WINNER_CATEGORY_ORDER,
    first_feasible_groups,
    framework_overview,
    framework_win_percentages,
    validate_selected_identities,
)


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


def test_first_feasible_groups_uses_smallest_candidate_g():
    trace = pd.DataFrame(
        {
            "candidate_g": [3, 1, 2],
            "classical_feasible": [True, False, True],
            "average_feasible": [True, False, False],
            "bayesian_feasible": [True, True, True],
        }
    )
    assert first_feasible_groups(trace) == {"Classical": 2, "Average": 3, "Bayesian": 1}


def test_framework_win_percentages_classifies_all_win_and_tie_types():
    comparisons = pd.DataFrame(
        [
            {"Classical": 1.0, "Average": 2.0, "Bayesian": 3.0},
            {"Classical": 2.0, "Average": 1.0, "Bayesian": 3.0},
            {"Classical": 2.0, "Average": 3.0, "Bayesian": 1.0},
            {"Classical": 3.0, "Average": 1.0, "Bayesian": 1.0},
            {"Classical": 1.0, "Average": 3.0, "Bayesian": 1.0},
            {"Classical": 1.0, "Average": 1.0, "Bayesian": 3.0},
            {"Classical": 1.0, "Average": 1.0, "Bayesian": 1.0},
        ]
    )
    result = framework_win_percentages(comparisons, higher_is_better=False).set_index("outcome")
    assert result.index.tolist() == list(WINNER_CATEGORY_ORDER)
    assert (result["count"] == 1).all()
    assert (result["percentage"] - 100.0 / 7.0).abs().max() < 1e-12
