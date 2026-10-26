"""Landing page for the GChSPFAM-GE-3RF research dashboard."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS
from src.metrics import framework_overview
from src.runtime import get_repository
from src.ui import render_data_source_badge, render_footer, render_page_header

st.set_page_config(
    page_title="GChSPFAM-GE-3RF Research Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_page_header(
    "GChSPFAM-GE-3RF Research Analytics",
    "Interactive exploration of consumer-risk-restricted Group Chain Sampling Plans under the corrected Generalized Exponential model.",
)

repository = get_repository()
render_data_source_badge(repository)

counts = repository.dataset_counts()
selected = repository.selected_plans()
overview = framework_overview(selected)

metric_columns = st.columns(5)
metric_columns[0].metric("Candidate records", f"{counts['candidate_records']:,}")
metric_columns[1].metric("Selected plans", f"{counts['selected_records']:,}")
metric_columns[2].metric("Matched units", f"{counts['matched_records']:,}")
metric_columns[3].metric("Frameworks", "3")
metric_columns[4].metric("Consumer-risk ceiling", "0.10")

st.subheader("Framework overview")
left, right = st.columns(2)
with left:
    figure = px.bar(
        overview,
        x="framework",
        y="mean_selected_g",
        color="framework",
        color_discrete_map=FRAMEWORK_COLORS,
        labels={"framework": "Framework", "mean_selected_g": "Mean selected g*"},
        text_auto=".3f",
    )
    st.plotly_chart(apply_academic_layout(figure, "Mean selected number of groups"), width="stretch")
with right:
    figure = px.bar(
        overview,
        x="framework",
        y="mean_l_p1",
        color="framework",
        color_discrete_map=FRAMEWORK_COLORS,
        labels={"framework": "Framework", "mean_l_p1": "Mean L(p₁)"},
        text_auto=".4f",
    )
    st.plotly_chart(
        apply_academic_layout(figure, "Mean acceptable-quality acceptance probability"),
        width="stretch",
    )

st.subheader("How to use this dashboard")
st.markdown(
    """
- **Selected Plan Explorer** inspects all six risks at each framework-selected plan.
- **Framework Comparison** performs matched comparisons without treating differently conditioned own risks as equivalent.
- **OC Explorer** examines fixed-plan acceptance across mean-life ratios.
- **Sensitivity Explorer** studies GE shape, termination multiplier, mean-life ratio, GChSP parameters, and Beta prior.
- **Candidate Explorer** traces all 500 group-count candidates and verifies first-feasible selection.
- **Chart Gallery** provides the complete set of 39 validated Stage 9 academic figures.
- **Validation & Downloads** exposes reproducibility evidence and research-ready extracts.
"""
)

st.info(
    "The dashboard is descriptive. It does not alter the consumer-risk-only optimization, impose producer-risk constraints, or optimize any risk sum."
)

render_footer()
