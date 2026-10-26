"""Descriptive transformations used by multiple dashboard pages."""

from __future__ import annotations

import pandas as pd

from src.constants import FRAMEWORKS


def framework_overview(selected: pd.DataFrame) -> pd.DataFrame:
    return (
        selected.groupby("framework", observed=True)
        .agg(
            records=("selected_g", "size"),
            mean_selected_g=("selected_g", "mean"),
            median_selected_g=("selected_g", "median"),
            mean_selected_n=("selected_n", "mean"),
            mean_own_pr=("framework_producer_risk", "mean"),
            mean_own_cr=("framework_consumer_risk", "mean"),
            mean_own_risk_sum=("framework_risk_sum", "mean"),
            mean_l_p1=("l_p1", "mean"),
        )
        .reindex(FRAMEWORKS)
        .reset_index()
    )


def long_risks(selected: pd.DataFrame) -> pd.DataFrame:
    columns = ["pr", "apr", "bpr", "cr", "acr", "bcr", "msr", "msar", "msbr"]
    identifiers = ["scenario_id", "prior_id", "framework", "selected_g", "selected_n"]
    return selected.melt(id_vars=identifiers, value_vars=columns, var_name="risk", value_name="value")


def validate_selected_identities(selected: pd.DataFrame, tolerance: float = 5e-12) -> dict[str, float | int]:
    risk_sum_error = max(
        float((selected["msr"] - selected["pr"] - selected["cr"]).abs().max()),
        float((selected["msar"] - selected["apr"] - selected["acr"]).abs().max()),
        float((selected["msbr"] - selected["bpr"] - selected["bcr"]).abs().max()),
    )
    return {
        "risk_sum_error": risk_sum_error,
        "lp1_error": float((selected["l_p1"] - (1.0 - selected["pr"])).abs().max()),
        "lp2_error": float((selected["l_p2"] - selected["cr"]).abs().max()),
        "sample_size_error": int(
            (selected["selected_n"] - selected["selected_g"] * selected["group_size_r"]).abs().max()
        ),
        "feasibility_failures": int(
            (selected["framework_consumer_risk"] > selected["consumer_risk_limit"] + tolerance).sum()
        ),
    }
