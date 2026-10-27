from __future__ import annotations

import pandas as pd

from src.ui import GLOBAL_FILTER_OPTIONS, NAVIGATION_LINKS, apply_global_filters


def test_sidebar_navigation_order_and_labels():
    assert [label for _path, label in NAVIGATION_LINKS] == [
        "INTRODUCTION",
        "OVERVIEW",
        "PHASES",
        "ALL CANDIDATE EXPLORER",
        "SELECTED PLAN EXPLORER",
        "SELECTED G EXPLORER",
        "L(P) EXPLORER",
        "SENSITIVITY EXPLORER",
        "COMPARISON 1.0",
        "COMPARISON 2.0",
        "CHART GALLERY",
        "DOWNLOADS",
    ]


def test_global_filter_options_cover_the_experimental_design():
    assert GLOBAL_FILTER_OPTIONS == {
        "prior_id": ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"],
        "acceptable_mean_life_ratio": [2, 4, 6, 8, 10, 12],
        "termination_multiplier": [0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00],
        "ge_shape": [1, 2, 3],
        "group_size_r": [2, 3, 4, 5],
        "chain_parameter_i": [1, 2, 3, 4],
    }


def test_global_filters_apply_to_standard_and_oc_ratio_columns(monkeypatch):
    monkeypatch.setattr(
        "src.ui.active_global_filters",
        lambda: {"prior_id": ["B1"], "acceptable_mean_life_ratio": [4]},
    )
    selected = pd.DataFrame(
        {
            "prior_id": ["B1", "B1", "B2"],
            "acceptable_mean_life_ratio": [2, 4, 4],
        }
    )
    filtered_selected = apply_global_filters(selected)
    assert filtered_selected.to_dict("records") == [{"prior_id": "B1", "acceptable_mean_life_ratio": 4}]

    oc = pd.DataFrame(
        {
            "prior_id": ["B1", "B1", "B2"],
            "evaluation_mean_life_ratio": [2, 4, 4],
        }
    )
    filtered_oc = apply_global_filters(oc, mean_ratio_column="evaluation_mean_life_ratio")
    assert filtered_oc.to_dict("records") == [{"prior_id": "B1", "evaluation_mean_life_ratio": 4}]
