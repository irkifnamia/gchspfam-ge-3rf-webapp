"""Descriptive transformations used by multiple dashboard pages."""

from __future__ import annotations

import pandas as pd

from src.constants import FRAMEWORKS

CANDIDATE_FEASIBILITY_COLUMNS = {
    "Classical": "classical_feasible",
    "Average": "average_feasible",
    "Bayesian": "bayesian_feasible",
}

WINNER_CATEGORY_ORDER = (
    "Bayesian win",
    "Average win",
    "Classical win",
    "Bayesian & Average tie",
    "Bayesian & Classical tie",
    "Average & Classical tie",
    "Three-way tie",
)

WINNER_LABELS = {
    frozenset({"Bayesian"}): "Bayesian win",
    frozenset({"Average"}): "Average win",
    frozenset({"Classical"}): "Classical win",
    frozenset({"Bayesian", "Average"}): "Bayesian & Average tie",
    frozenset({"Bayesian", "Classical"}): "Bayesian & Classical tie",
    frozenset({"Average", "Classical"}): "Average & Classical tie",
    frozenset(FRAMEWORKS): "Three-way tie",
}


def first_feasible_groups(trace: pd.DataFrame) -> dict[str, int | None]:
    """Return the smallest feasible candidate g for each risk framework."""
    required = {"candidate_g", *CANDIDATE_FEASIBILITY_COLUMNS.values()}
    missing = required.difference(trace.columns)
    if missing:
        raise ValueError(f"Candidate trace is missing required columns: {sorted(missing)}")

    ordered = trace.sort_values("candidate_g", kind="stable")
    selected: dict[str, int | None] = {}
    for framework, feasible_column in CANDIDATE_FEASIBILITY_COLUMNS.items():
        feasible = ordered.loc[ordered[feasible_column].astype(bool), "candidate_g"]
        selected[framework] = None if feasible.empty else int(feasible.iloc[0])
    return selected


def framework_win_percentages(
    wide: pd.DataFrame,
    *,
    higher_is_better: bool,
    tolerance: float = 0.0,
) -> pd.DataFrame:
    """Classify three-framework wins and ties for complete matched rows."""
    missing = set(FRAMEWORKS).difference(wide.columns)
    if missing:
        raise ValueError(f"Comparison table is missing framework columns: {sorted(missing)}")

    complete = wide[list(FRAMEWORKS)].dropna()
    labels: list[str] = []
    for values in complete.itertuples(index=False, name=None):
        target = max(values) if higher_is_better else min(values)
        winners = frozenset(
            framework for framework, value in zip(FRAMEWORKS, values, strict=True) if abs(value - target) <= tolerance
        )
        labels.append(WINNER_LABELS[winners])

    counts = pd.Series(labels, dtype="string").value_counts().reindex(WINNER_CATEGORY_ORDER, fill_value=0)
    result = counts.rename_axis("outcome").reset_index(name="count")
    denominator = len(complete)
    result["percentage"] = 0.0 if denominator == 0 else 100.0 * result["count"] / denominator
    return result


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
