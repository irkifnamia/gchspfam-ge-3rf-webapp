"""Reproducibility evidence and validated extracts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.constants import EXPECTED_COUNTS
from src.metrics import validate_selected_identities
from src.repository import assert_expected_counts
from src.runtime import get_repository
from src.ui import dataframe_download, render_data_source_badge, render_footer, render_page_header

st.set_page_config(page_title="Validation and Downloads", page_icon="✅", layout="wide")
render_page_header(
    "Validation and Reproducibility",
    "Confirm data integrity, mathematical identities, source provenance, and downloadable research extracts.",
)
repository = get_repository()
render_data_source_badge(repository)
counts = repository.dataset_counts()
selected = repository.selected_plans()
matched = repository.matched_results()
identities = validate_selected_identities(selected)
deployment_path = Path(__file__).resolve().parents[1] / "data" / "neon_deployment_validation.json"
deployment = json.loads(deployment_path.read_text(encoding="utf-8")) if deployment_path.is_file() else {}

count_rows = [
    {
        "dataset": name,
        "observed": counts.get(name),
        "expected": expected,
        "status": "PASS" if counts.get(name) == expected else "FAIL",
    }
    for name, expected in EXPECTED_COUNTS.items()
]
st.subheader("Dataset contract")
st.dataframe(pd.DataFrame(count_rows), width="stretch", hide_index=True)

try:
    assert_expected_counts(counts)
    st.success("All authoritative record counts match the validated research package.")
except ValueError as exc:
    st.error(str(exc))

st.subheader("Selected-plan mathematical identities")
identity_rows = pd.DataFrame(
    [
        {
            "check": "Maximum risk-sum identity error",
            "value": identities["risk_sum_error"],
            "status": "PASS" if identities["risk_sum_error"] <= 5e-12 else "FAIL",
        },
        {
            "check": "Maximum L(p₁)=1−PR error",
            "value": identities["lp1_error"],
            "status": "PASS" if identities["lp1_error"] <= 5e-12 else "FAIL",
        },
        {
            "check": "Maximum L(p₂)=CR error",
            "value": identities["lp2_error"],
            "status": "PASS" if identities["lp2_error"] <= 5e-12 else "FAIL",
        },
        {
            "check": "Maximum n*=r×g* error",
            "value": identities["sample_size_error"],
            "status": "PASS" if identities["sample_size_error"] == 0 else "FAIL",
        },
        {
            "check": "Consumer-risk feasibility failures",
            "value": identities["feasibility_failures"],
            "status": "PASS" if identities["feasibility_failures"] == 0 else "FAIL",
        },
    ]
)
st.dataframe(identity_rows, width="stretch", hide_index=True)

summary = repository.validation_summary()
if summary:
    st.subheader("Stage 10 final verification")
    metrics = summary.get("metrics", {})
    columns = st.columns(4)
    columns[0].metric("Overall status", summary.get("overall_status", "Unknown"))
    columns[1].metric("Independent cases", f"{metrics.get('independent_cases', 0):,}")
    columns[2].metric(
        "Maximum absolute discrepancy", f"{metrics.get('independent_max_absolute_error', float('nan')):.3e}"
    )
    columns[3].metric("Warnings", len(summary.get("warnings", [])))
    with st.expander("Documented warnings and limitations"):
        for warning in summary.get("warnings", []):
            st.write(f"- {warning}")

if deployment:
    st.subheader("Neon deployment validation")
    database = deployment["database"]
    parity = deployment["source_parity"]
    role = deployment["readonly_role"]
    columns = st.columns(5)
    columns[0].metric("Deployment status", deployment["overall_status"])
    columns[1].metric("Candidate rows", f"{database['candidate_records']:,}")
    columns[2].metric("Database size", f"{database['database_mib']:.2f} MiB")
    columns[3].metric("Source mismatches", parity["candidate_sample_cell_mismatches"])
    columns[4].metric("Read-only role", "PASS" if role["select"] and not role["insert"] else "FAIL")
    st.caption(
        "Transport parity used all selected, matched, and fixed-OC records plus 25,920 deterministic candidate rows "
        "covering g ∈ {1, 2, 250, 499, 500} for every prior–scenario unit."
    )

st.subheader("Research-ready downloads")
left, right = st.columns(2)
with left:
    dataframe_download(selected, "selected_plans_research_ready.csv", "Download all selected plans")
with right:
    dataframe_download(matched, "matched_framework_results.csv", "Download matched framework results")

st.info(
    "The complete 2,592,000-row candidate dataset is intentionally downloaded through filtered All Candidate Explorer extracts or the authoritative Parquet archive, not materialized in browser memory."
)
render_footer()
