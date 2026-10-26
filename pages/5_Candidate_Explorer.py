"""Column-selectable exploration of every candidate g for one research unit."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS
from src.runtime import get_repository
from src.ui import dataframe_download, render_data_source_badge, render_footer, render_page_header

st.set_page_config(page_title="All Candidate Explorer", page_icon="🧪", layout="wide")
render_page_header(
    "All Candidate Explorer",
    "Inspect all 500 candidate group counts, choose the exact columns to display, and verify first-feasible selection.",
)
repository = get_repository()
render_data_source_badge(repository)
index = repository.scenario_prior_index()

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
selected_columns = st.multiselect(
    "Columns to display",
    options=trace.columns.tolist(),
    default=[column for column in default_columns if column in trace.columns],
)
g_min = int(trace["candidate_g"].min())
g_max = int(trace["candidate_g"].max())
g_range = st.slider("Candidate g range", g_min, g_max, (g_min, g_max))
view = trace[trace["candidate_g"].between(*g_range)]
if selected_columns:
    displayed = view[selected_columns]
    st.caption(f"Showing {len(displayed):,} candidate records and {len(selected_columns)} selected columns.")
    st.dataframe(displayed, width="stretch", height=520, hide_index=True)
    dataframe_download(
        displayed,
        f"candidate_view_{scenario_id}_{loaded_prior}_g{g_range[0]}-{g_range[1]}.csv",
        "Download displayed candidate view",
    )
else:
    st.warning("Select at least one column to display the candidate table.")

st.subheader("Risk trajectories and minimality")
consumer = trace[["candidate_g", "cr", "acr", "bcr"]].rename(
    columns={"cr": "Classical", "acr": "Average", "bcr": "Bayesian"}
)
consumer_long = consumer.melt(id_vars="candidate_g", var_name="framework", value_name="consumer_risk")
figure = px.line(
    consumer_long,
    x="candidate_g",
    y="consumer_risk",
    color="framework",
    color_discrete_map=FRAMEWORK_COLORS,
    labels={"candidate_g": "Candidate g", "consumer_risk": "Framework-specific consumer risk"},
)
figure.add_hline(y=0.10, line_dash="dash", line_color="#A33A3A", annotation_text="Risk ceiling 0.10")
st.plotly_chart(apply_academic_layout(figure, "Consumer-risk trajectories"), width="stretch")

mapping = {
    "Classical": ("cr", "classical_feasible", "pr"),
    "Average": ("acr", "average_feasible", "apr"),
    "Bayesian": ("bcr", "bayesian_feasible", "bpr"),
}
minimality_rows = []
for framework, (consumer_column, feasible_column, producer_column) in mapping.items():
    feasible = trace[trace[feasible_column]]
    selected = feasible.iloc[0]
    previous = trace[trace.candidate_g == selected.candidate_g - 1]
    minimality_rows.append(
        {
            "framework": framework,
            "selected_g": int(selected.candidate_g),
            "selected_n": int(selected.candidate_n),
            "own_consumer_risk_at_g*": float(selected[consumer_column]),
            "own_producer_risk_at_g*": float(selected[producer_column]),
            "risk_at_g*-1": None if previous.empty else float(previous.iloc[0][consumer_column]),
            "g*-1_fails": True if previous.empty else bool(previous.iloc[0][consumer_column] > 0.10),
        }
    )
minimality = pd.DataFrame(minimality_rows)
st.dataframe(minimality, width="stretch", hide_index=True)

producer = trace[["candidate_g", "pr", "apr", "bpr"]].rename(
    columns={"pr": "Classical", "apr": "Average", "bpr": "Bayesian"}
)
producer_long = producer.melt(id_vars="candidate_g", var_name="framework", value_name="producer_risk")
figure = px.line(
    producer_long,
    x="candidate_g",
    y="producer_risk",
    color="framework",
    color_discrete_map=FRAMEWORK_COLORS,
    labels={"candidate_g": "Candidate g", "producer_risk": "Framework-specific producer risk"},
)
st.plotly_chart(apply_academic_layout(figure, "Producer-risk evaluation (not constrained)"), width="stretch")

st.info(
    "The red line is the only optimization restriction. Producer risks and risk sums are shown for evaluation and do not affect g*."
)
dataframe_download(
    trace, f"candidate_trace_{scenario_id}_{loaded_prior}.csv", "Download full 31-column candidate trace"
)
render_footer()
