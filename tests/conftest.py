from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.repository import LocalResultsRepository


@pytest.fixture
def selected_frame() -> pd.DataFrame:
    rows = []
    for framework, g, pr, cr, apr, acr, bpr, bcr in [
        ("Classical", 3, 0.2, 0.08, 0.1, 0.07, 0.3, 0.06),
        ("Average", 2, 0.1, 0.15, 0.2, 0.09, 0.4, 0.08),
        ("Bayesian", 1, 0.05, 0.4, 0.1, 0.3, 0.2, 0.09),
    ]:
        rows.append(
            {
                "scenario_id": "S001",
                "prior_id": "B1",
                "prior_mean": 0.032,
                "prior_sd": 0.047,
                "beta_alpha": 0.4,
                "beta_beta": 12.6,
                "acceptable_mean_life_ratio": 2.0,
                "termination_multiplier": 0.25,
                "ge_shape": 1.0,
                "group_size_r": 2,
                "chain_parameter_i": 1,
                "p1": 0.1,
                "p2": 0.2,
                "framework": framework,
                "consumer_risk_limit": 0.1,
                "feasible": True,
                "selected_g": g,
                "selected_n": 2 * g,
                "pr": pr,
                "apr": apr,
                "bpr": bpr,
                "cr": cr,
                "acr": acr,
                "bcr": bcr,
                "msr": pr + cr,
                "msar": apr + acr,
                "msbr": bpr + bcr,
                "l_p1": 1 - pr,
                "l_p2": cr,
                "framework_producer_risk": {"Classical": pr, "Average": apr, "Bayesian": bpr}[framework],
                "framework_consumer_risk": {"Classical": cr, "Average": acr, "Bayesian": bcr}[framework],
                "framework_risk_sum": {"Classical": pr + cr, "Average": apr + acr, "Bayesian": bpr + bcr}[framework],
                "consumer_risk_margin": 0.01,
                "numerical_validation_status": "PASS",
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture
def local_repository(tmp_path: Path, selected_frame: pd.DataFrame) -> LocalResultsRepository:
    results = tmp_path / "results"
    analytics = results / "outputs" / "analytics"
    candidates = results / "outputs" / "candidates" / "stage6_parquet"
    fixed = results / "outputs" / "stage9" / "data"
    analytics.mkdir(parents=True)
    candidates.mkdir(parents=True)
    fixed.mkdir(parents=True)
    selected_frame.to_parquet(analytics / "selected_plans_research_ready.parquet", index=False)
    selected_frame.iloc[[0]][["scenario_id", "prior_id"]].to_parquet(
        analytics / "matched_framework_results.parquet", index=False
    )
    pd.DataFrame(
        {
            "scenario_id": ["S001", "S001"],
            "prior_id": ["B1", "B1"],
            "candidate_g": [1, 2],
            "candidate_n": [2, 4],
            "cr": [0.2, 0.08],
            "acr": [0.15, 0.09],
            "bcr": [0.09, 0.04],
            "classical_feasible": [False, True],
            "average_feasible": [False, True],
            "bayesian_feasible": [True, True],
        }
    ).to_parquet(candidates / "part-0000.parquet", index=False)
    pd.DataFrame(
        {
            "fixed_plan_id": ["X"],
            "prior_id": ["B1"],
            "framework": ["Classical"],
            "evaluation_mean_life_ratio": [2.0],
            "l_p": [0.8],
        }
    ).to_csv(fixed / "fixed_plan_oc_evaluations.csv", index=False)
    return LocalResultsRepository(results, tmp_path / "app")
