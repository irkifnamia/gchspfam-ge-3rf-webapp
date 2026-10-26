"""Candidate-level risk trajectories and minimality verification."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS
from src.runtime import get_repository
from src.ui import dataframe_download, render_data_source_badge, render_footer, render_page_header

st.set_page_config(page_title="Candidate Explorer", page_icon="🧪", layout="wide")
render_page_header(
    "Candidate-Level Minimality Explorer",
    "Trace consumer and producer risks over g=1,…,500 and verify each framework's first feasible plan.",
)
repository = get_repository()
render_data_source_badge(repository)
index = repository.scenario_prior_index()

selectors = st.columns(6)
prior = selectors[0].selectbox("Prior", sorted(index.prior_id.unique()))
ratio = selectors[1].selectbox("ρA", sorted(index.acceptable_mean_life_ratio.unique()))
termination = selectors[2].selectbox("a", sorted(index.termination_multiplier.unique()))
shape = selectors[3].selectbox("λ", sorted(index.ge_shape.unique()))
group_size = selectors[4].selectbox("r", sorted(index.group_size_r.unique()))
chain = selectors[5].selectbox("i", sorted(index.chain_parameter_i.unique()))

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

scenario_id = str(chosen.iloc[0].scenario_id)
with st.spinner(f"Loading the 500 candidates for {scenario_id} / {prior}…"):
    trace = repository.candidate_trace(scenario_id, prior)

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
dataframe_download(trace, f"candidate_trace_{scenario_id}_{prior}.csv")
render_footer()
