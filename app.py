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
    page_title="Overview",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_page_header(
    "Overview",
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
- **Phases** documents the validated Phase 3–9 mathematical workflow with collapsible details.
- **All Candidate Explorer** displays any chosen subset of the 31 candidate columns across all 500 group counts.
- **Selected Plan Explorer** provides an industry-oriented review of one specific sampling plan.
- **Selected g Explorer** presents CR, ACR, and BCR candidate tables and matched-scenario g* heatmaps.
- **OC Explorer** examines fixed-plan acceptance across mean-life ratios.
- **Sensitivity Explorer** studies GE shape, termination multiplier, mean-life ratio, GChSP parameters, and Beta prior.
- **General Comparison** performs matched comparisons without treating differently conditioned own risks as equivalent.
- **Head-to-Head Comparison** reports three-framework g* and L(p) wins and ties for matched or all-available records.
- **Chart Gallery** provides the complete set of 39 validated Stage 9 academic figures.
- **Downloads** provides research-ready extracts for offline use.
"""
)

st.info(
    "The dashboard is descriptive. It does not alter the consumer-risk-only optimization, impose producer-risk constraints, or optimize any risk sum."
)

render_footer()
