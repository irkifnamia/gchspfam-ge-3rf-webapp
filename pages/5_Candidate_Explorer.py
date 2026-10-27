"""Column-selectable exploration of every candidate g for one research unit."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.runtime import get_repository
from src.ui import apply_global_filters, dataframe_download, render_data_source_badge, render_footer, render_page_header

RISK_GRADIENTS = {
    "pr": ("#EAF2FB", "#17365D"),
    "apr": ("#EAF6EF", "#2E7D5B"),
    "bpr": ("#FFF7D6", "#C69200"),
    "cr": ("#F2ECF9", "#6A3D9A"),
    "acr": ("#FFF0E3", "#C75B12"),
    "bcr": ("#FDEBEC", "#B4232D"),
}


def gradient_styles(series: pd.Series, light: str, dark: str) -> list[str]:
    """Return dependency-free gradient CSS for one numerical risk column."""
    minimum = float(series.min())
    maximum = float(series.max())
    span = maximum - minimum
    light_rgb = tuple(int(light[index : index + 2], 16) for index in (1, 3, 5))
    dark_rgb = tuple(int(dark[index : index + 2], 16) for index in (1, 3, 5))
    styles = []
    for value in series.astype(float):
        weight = 0.0 if span == 0 else (value - minimum) / span
        rgb = tuple(round(start + weight * (end - start)) for start, end in zip(light_rgb, dark_rgb, strict=True))
        foreground = "#FFFFFF" if weight >= 0.58 else "#17202A"
        styles.append(f"background-color: rgb{rgb}; color: {foreground}")
    return styles


def style_candidate_table(frame):
    """Apply a distinct within-column gradient to each displayed risk measure."""
    risk_columns = [column for column in RISK_GRADIENTS if column in frame.columns]
    styled = frame.style.format({column: "{:.8f}" for column in risk_columns})
    for column in risk_columns:
        light, dark = RISK_GRADIENTS[column]
        styled = styled.apply(
            lambda series, light=light, dark=dark: gradient_styles(series, light, dark),
            subset=[column],
            axis=0,
        )
    return styled


st.set_page_config(page_title="All Candidate Explorer", page_icon="🧪", layout="wide")
render_page_header(
    "All Candidate Explorer",
    "Inspect all 500 candidate group counts, choose the exact columns to display, and verify first-feasible selection.",
)
repository = get_repository()
render_data_source_badge(repository)
index = apply_global_filters(repository.scenario_prior_index())
if index.empty:
    st.warning("No prior–scenario units match the active global filters.")
    st.stop()

st.caption(
    "Candidate rows are queried from Neon only after you click Load. "
    "The first request after inactivity may take several seconds; recent traces are cached."
)
with st.form("candidate_trace_selector"):
    selectors = st.columns(6)
    prior = selectors[0].selectbox("Prior", sorted(index.prior_id.unique()))
    ratio = selectors[1].selectbox("ρA", sorted(index.acceptable_mean_life_ratio.unique()))
    termination = selectors[2].selectbox("a", sorted(index.termination_multiplier.unique()))
    shape = selectors[3].selectbox("λ", sorted(index.ge_shape.unique()))
    group_size = selectors[4].selectbox("r", sorted(index.group_size_r.unique()))
    chain = selectors[5].selectbox("i", sorted(index.chain_parameter_i.unique()))
    load_requested = st.form_submit_button("Load candidate trace", type="primary")

if load_requested:
    chosen = index[
        (index.prior_id == prior)
        & (index.acceptable_mean_life_ratio == ratio)
        & (index.termination_multiplier == termination)
        & (index.ge_shape == shape)
        & (index.group_size_r == group_size)
        & (index.chain_parameter_i == chain)
    ]
    if chosen.empty:
        st.error("The selected combination is not a valid experimental unit.")
        st.stop()
    st.session_state["candidate_trace_selection"] = {
        "scenario_id": str(chosen.iloc[0].scenario_id),
        "prior_id": str(prior),
    }

selection = st.session_state.get("candidate_trace_selection")
if selection is None:
    st.info("Choose one prior–scenario combination, then click **Load candidate trace**.")
    render_footer()
    st.stop()

scenario_id = selection["scenario_id"]
loaded_prior = selection["prior_id"]
with st.spinner(f"Loading the 500 candidates for {scenario_id} / {loaded_prior}…"):
    trace = repository.candidate_trace(scenario_id, loaded_prior)
st.caption(f"Loaded prior–scenario unit: {scenario_id} / {loaded_prior}")

st.subheader("Candidate data view")
default_columns = [
    "scenario_id",
    "prior_id",
    "acceptable_mean_life_ratio",
    "termination_multiplier",
    "ge_shape",
    "group_size_r",
    "chain_parameter_i",
    "candidate_g",
    "candidate_n",
    "pr",
    "apr",
    "bpr",
    "cr",
    "acr",
    "bcr",
    "classical_feasible",
    "average_feasible",
    "bayesian_feasible",
]
with st.expander("Choose columns to display", expanded=False):
    selected_columns = st.multiselect(
        "Candidate-table columns",
        options=trace.columns.tolist(),
        default=[column for column in default_columns if column in trace.columns],
        help="Select the required columns, then collapse this panel to maximize table space.",
    )
g_min = int(trace["candidate_g"].min())
g_max = int(trace["candidate_g"].max())
g_range = st.slider("Candidate g range", g_min, g_max, (g_min, g_max))
view = trace[trace["candidate_g"].between(*g_range)]
if selected_columns:
    displayed = view[selected_columns]
    st.caption(f"Showing {len(displayed):,} candidate records and {len(selected_columns)} selected columns.")
    st.dataframe(style_candidate_table(displayed), width="stretch", height=520, hide_index=True)
    st.caption(
        "Risk gradients: PR—blue, APR—green, BPR—gold, CR—purple, ACR—orange, and BCR—red. "
        "Darker shading indicates a larger value within the currently displayed candidate range."
    )
    dataframe_download(
        displayed,
        f"candidate_view_{scenario_id}_{loaded_prior}_g{g_range[0]}-{g_range[1]}.csv",
        "Download displayed candidate view",
    )
else:
    st.warning("Select at least one column to display the candidate table.")

dataframe_download(
    trace, f"candidate_trace_{scenario_id}_{loaded_prior}.csv", "Download full 31-column candidate trace"
)
render_footer()
