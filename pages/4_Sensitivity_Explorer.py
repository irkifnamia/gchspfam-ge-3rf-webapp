"""Interactive sensitivity summaries across the experimental factors."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS
from src.runtime import get_repository
from src.ui import render_data_source_badge, render_footer, render_page_header, sidebar_filters

st.set_page_config(page_title="Sensitivity Explorer", page_icon="🧭", layout="wide")
render_page_header(
    "Sensitivity Explorer",
    "Explore how selected plans and performance measures vary across the complete factorial design.",
)
repository = get_repository()
render_data_source_badge(repository)
filters = sidebar_filters(repository.filter_options())
data = repository.selected_plans(filters)

if data.empty:
    st.warning("No records satisfy the current filters.")
    st.stop()

dimension_options = {
    "GE shape λ": ["ge_shape"],
    "Termination multiplier a": ["termination_multiplier"],
    "Mean-life ratio ρA": ["acceptable_mean_life_ratio"],
    "Beta prior": ["prior_id"],
    "GChSP pair (r, i)": ["group_size_r", "chain_parameter_i"],
}
metric_options = {
    "Selected g*": "selected_g",
    "Selected n*": "selected_n",
    "L(p₁)": "l_p1",
    "Own producer risk": "framework_producer_risk",
    "Own consumer risk": "framework_consumer_risk",
    "Own risk sum": "framework_risk_sum",
    "Classical PR": "pr",
    "Average APR": "apr",
    "Bayesian BPR": "bpr",
    "Classical CR": "cr",
    "Average ACR": "acr",
    "Bayesian BCR": "bcr",
}

controls = st.columns(3)
dimension_label = controls[0].selectbox("Sensitivity dimension", list(dimension_options))
metric_label = controls[1].selectbox("Performance measure", list(metric_options))
statistic = controls[2].selectbox("Summary", ["Mean", "Median"])

dimensions = dimension_options[dimension_label]
metric = metric_options[metric_label]
if len(dimensions) == 2:
    data = data.assign(gchsp_pair="r=" + data.group_size_r.astype(str) + ", i=" + data.chain_parameter_i.astype(str))
    x_column = "gchsp_pair"
else:
    x_column = dimensions[0]

aggregation = "mean" if statistic == "Mean" else "median"
summary = data.groupby([x_column, "framework"], observed=True)[metric].agg(aggregation).rename("value").reset_index()

figure = px.line(
    summary,
    x=x_column,
    y="value",
    color="framework",
    markers=True,
    color_discrete_map=FRAMEWORK_COLORS,
    category_orders={"framework": list(FRAMEWORK_COLORS)},
    labels={x_column: dimension_label, "value": f"{statistic} {metric_label}", "framework": "Framework"},
)
st.plotly_chart(
    apply_academic_layout(figure, f"{metric_label} sensitivity to {dimension_label}"),
    width="stretch",
)

st.dataframe(summary, width="stretch", hide_index=True)
if metric.startswith("framework_"):
    st.warning(
        "The displayed own-risk series use framework-specific conditioning. Compare their behavior descriptively; "
        "do not interpret their absolute magnitudes as the same risk functional."
    )
render_footer()
