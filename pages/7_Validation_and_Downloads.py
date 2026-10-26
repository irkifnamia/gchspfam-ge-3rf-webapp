"""Download research-ready datasets, candidate traces, and academic charts."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import streamlit as st

from src.runtime import get_repository
from src.ui import apply_global_filters, dataframe_download, render_page_header


@st.cache_data(show_spinner=False)
def chart_archive(paths: tuple[str, ...]) -> bytes:
    """Create one deterministic ZIP archive from the packaged chart files."""
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for path_text in paths:
            path = Path(path_text)
            archive.write(path, arcname=path.name)
    return buffer.getvalue()


st.set_page_config(page_title="Downloads", page_icon="⬇️", layout="wide")
render_page_header(
    "Downloads",
    "Download research-ready selected plans, matched results, OC evaluations, candidate traces, and figures.",
)

repository = get_repository()
selected = apply_global_filters(repository.selected_plans())
matched = apply_global_filters(repository.matched_results())
fixed_oc = apply_global_filters(repository.fixed_plan_oc(), mean_ratio_column="evaluation_mean_life_ratio")

st.subheader("Research-ready analytical datasets")
cards = st.columns(3)
with cards[0]:
    st.markdown("#### Selected plans")
    st.metric("Records", f"{len(selected):,}")
    st.write("All Classical, Average, and Bayesian framework-selected plans with all six risks and three risk sums.")
    dataframe_download(selected, "selected_plans_research_ready.csv", "Download selected plans (CSV)")
with cards[1]:
    st.markdown("#### Matched framework results")
    st.metric("Prior–scenario units", f"{len(matched):,}")
    st.write("One wide record per matched prior–scenario unit for direct three-framework comparison.")
    dataframe_download(matched, "matched_framework_results.csv", "Download matched results (CSV)")
with cards[2]:
    st.markdown("#### Fixed-plan OC evaluations")
    st.metric("Records", f"{len(fixed_oc):,}")
    st.write("Acceptance probabilities for each selected plan across the six evaluation mean-life ratios.")
    dataframe_download(fixed_oc, "fixed_plan_oc_evaluations.csv", "Download fixed-plan OC (CSV)")

st.divider()
st.subheader("Candidate-level extract")
st.write(
    "Choose one prior–scenario unit to download all 500 candidate group counts and all candidate-level risk measures."
)
index = apply_global_filters(repository.scenario_prior_index())
if index.empty:
    st.info("No candidate units match the active global filters.")
    st.stop()
with st.form("download_candidate_selector"):
    controls = st.columns(2)
    prior_id = controls[0].selectbox("Beta prior", sorted(index["prior_id"].unique()))
    scenario_id = controls[1].selectbox("Scenario", sorted(index["scenario_id"].unique()))
    prepare_candidate = st.form_submit_button("Prepare candidate extract", type="primary")

if prepare_candidate:
    valid = index[(index["scenario_id"] == scenario_id) & (index["prior_id"] == prior_id)]
    if valid.empty:
        st.error("The selected scenario and prior do not form a valid research unit.")
    else:
        st.session_state["download_candidate_selection"] = (str(scenario_id), str(prior_id))

candidate_selection = st.session_state.get("download_candidate_selection")
if candidate_selection is not None:
    loaded_scenario, loaded_prior = candidate_selection
    with st.spinner(f"Preparing 500 candidate records for {loaded_scenario} / {loaded_prior}…"):
        candidate_trace = repository.candidate_trace(loaded_scenario, loaded_prior)
    st.success(f"Candidate extract ready: {loaded_scenario} / {loaded_prior} · {len(candidate_trace):,} records")
    dataframe_download(
        candidate_trace,
        f"candidate_trace_{loaded_scenario}_{loaded_prior}.csv",
        "Download candidate trace (CSV)",
    )

st.divider()
st.subheader("Academic figures")
chart_paths = repository.chart_paths()
st.write(f"Download the complete collection of {len(chart_paths)} high-resolution research figures as one ZIP file.")
if chart_paths:
    archive = chart_archive(tuple(str(path) for path in chart_paths))
    st.download_button(
        "Download all academic charts (ZIP)",
        data=archive,
        file_name="gchspfam_ge_3rf_academic_charts.zip",
        mime="application/zip",
    )
else:
    st.warning("No packaged chart files are currently available for download.")
