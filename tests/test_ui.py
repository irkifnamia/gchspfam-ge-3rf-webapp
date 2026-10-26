from __future__ import annotations

from src.ui import NAVIGATION_LINKS


def test_sidebar_navigation_order_and_labels():
    assert [label for _path, label in NAVIGATION_LINKS] == [
        "PHASES",
        "OVERVIEW",
        "ALL CANDIDATE EXPLORER",
        "SELECTED PLAN EXPLORER",
        "SELECTED G EXPLORER",
        "OC EXPLORER",
        "SENSITIVITY EXPLORER",
        "GENERAL COMPARISON",
        "HEAD-TO-HEAD COMPARISON",
        "CHART GALLERY",
        "DOWNLOADS",
    ]
