"""Three-framework overview for the GChSPFAM-GE-3RF dashboard."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS
from src.metrics import framework_overview
from src.runtime import get_repository
from src.ui import apply_global_filters, render_data_source_badge, render_footer, render_page_header

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")
render_page_header(
    "Overview",
    "Review the three risk frameworks across the currently filtered validated results.",
)

repository = get_repository()
render_data_source_badge(repository)
selected = apply_global_filters(repository.selected_plans())
if selected.empty:
    st.warning("No research records match the active global filters.")
    st.stop()

overview = framework_overview(selected)

st.header("Three Risk Frameworks Overview")
framework_columns = st.columns(3)
with framework_columns[0]:
    st.markdown(
        """
        **Classical**

        Evaluates producer and consumer risks at two fixed values of the fraction defective representing
        acceptable and limiting quality. It does not use a Beta prior.
        """
    )
with framework_columns[1]:
    st.markdown(
        """
        **Average**

        Averages the OC-based risks over the relevant good- and bad-quality regions under a
        Beta distribution, conditional on being inside each region.
        """
    )
with framework_columns[2]:
    st.markdown(
        """
        **Bayesian**

        Uses the same Beta prior and expresses producer and consumer risks as posterior-style
        conditional probabilities following rejection or acceptance.
        """
    )

left, right = st.columns(2)
with left:
    figure = px.bar(
        overview,
        x="framework",
        y="mean_selected_g",
        color="framework",
        color_discrete_map=FRAMEWORK_COLORS,
        labels={"framework": "Framework", "mean_selected_g": "Mean selected g⁎"},
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

render_footer()
