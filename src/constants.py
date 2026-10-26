"""Shared labels, colors, and validated data contracts."""

from __future__ import annotations

FRAMEWORKS = ("Classical", "Average", "Bayesian")
FRAMEWORK_COLORS = {
    "Classical": "#17365D",
    "Average": "#4C78A8",
    "Bayesian": "#C9A227",
}
PAIRWISE_COLORS = {"Lower": "#4C78A8", "Equal": "#D9D9D9", "Higher": "#C9A227"}

RISK_LABELS = {
    "pr": "PR",
    "apr": "APR",
    "bpr": "BPR",
    "cr": "CR",
    "acr": "ACR",
    "bcr": "BCR",
    "msr": "MSR",
    "msar": "MSAR",
    "msbr": "MSBR",
}

FILTER_COLUMNS = (
    "prior_id",
    "acceptable_mean_life_ratio",
    "termination_multiplier",
    "ge_shape",
    "group_size_r",
    "chain_parameter_i",
    "framework",
)

CANDIDATE_PRIMARY_KEY = ("scenario_id", "prior_id", "candidate_g")
SELECTED_PRIMARY_KEY = ("scenario_id", "prior_id", "framework")
MATCHED_PRIMARY_KEY = ("scenario_id", "prior_id")

EXPECTED_COUNTS = {
    "candidate_records": 2_592_000,
    "selected_records": 15_552,
    "matched_records": 5_184,
    "candidate_partitions": 48,
    "charts": 39,
}
