"""Matched framework comparisons and direction counts."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS, PAIRWISE_COLORS
from src.runtime import get_repository
from src.ui import apply_global_filters, render_data_source_badge, render_footer, render_page_header

st.set_page_config(page_title="Comparison 1.0", page_icon="⚖️", layout="wide")
render_page_header(
    "Comparison 1.0",
    "Compare Classical, Average, and Bayesian plans on the same prior–scenario units.",
)
repository = get_repository()
render_data_source_badge(repository)
data = apply_global_filters(repository.selected_plans())

if data.empty:
    st.warning("No matched units satisfy the current filters.")
    st.stop()

metric_options = {
    "Selected g⁎": "selected_g",
    "Selected n⁎": "selected_n",
    "L(p₁)": "l_p1",
    "PR": "pr",
    "APR": "apr",
    "BPR": "bpr",
    "CR": "cr",
    "ACR": "acr",
    "BCR": "bcr",
    "MSR": "msr",
    "MSAR": "msar",
    "MSBR": "msbr",
    "Own producer risk": "framework_producer_risk",
    "Own consumer risk": "framework_consumer_risk",
    "Own risk sum": "framework_risk_sum",
}
metric_label = st.selectbox("Comparison metric", list(metric_options))
metric = metric_options[metric_label]

summary = data.groupby("framework", observed=True)[metric].agg(["count", "mean", "median", "min", "max"]).reset_index()
columns = st.columns(3)
for position, framework in enumerate(FRAMEWORK_COLORS):
    row = summary[summary.framework == framework].iloc[0]
    columns[position].metric(framework, f"{row['mean']:.6g}", help=f"Median: {row['median']:.6g}")

left, right = st.columns([1.15, 1])
with left:
    figure = px.box(
        data,
        x="framework",
        y=metric,
        color="framework",
        color_discrete_map=FRAMEWORK_COLORS,
        points=False,
        category_orders={"framework": list(FRAMEWORK_COLORS)},
        labels={"framework": "Framework", metric: metric_label},
    )
    st.plotly_chart(apply_academic_layout(figure, f"Matched distribution: {metric_label}"), width="stretch")

with right:
    st.markdown(f"#### Direction of {metric_label} differences")
    comparison = st.selectbox(
        "Pairwise direction", ["Bayesian vs Classical", "Bayesian vs Average", "Average vs Classical"]
    )
    first, second = comparison.split(" vs ")
    pivot = data.pivot(index=["scenario_id", "prior_id"], columns="framework", values=metric).dropna()
    difference = pivot[first] - pivot[second]
    tolerance = 0.0 if metric in {"selected_g", "selected_n"} else 5e-12
    direction = np.where(difference < -tolerance, "Lower", np.where(difference > tolerance, "Higher", "Equal"))
    direction_table = (
        pd.Series(direction)
        .value_counts()
        .reindex(["Lower", "Equal", "Higher"], fill_value=0)
        .rename_axis("direction")
        .reset_index(name="count")
    )
    direction_table["percentage"] = 100.0 * direction_table["count"] / len(difference)
    figure = px.bar(
        direction_table,
        x="percentage",
        y=pd.Series([comparison] * 3),
        color="direction",
        orientation="h",
        color_discrete_map=PAIRWISE_COLORS,
        category_orders={"direction": ["Lower", "Equal", "Higher"]},
        text=direction_table["percentage"].map(lambda value: f"{value:.1f}%" if value >= 4 else ""),
        labels={"x": "Percentage", "y": "", "direction": "First framework is"},
    )
    figure.update_layout(barmode="stack")
    figure = apply_academic_layout(figure, "")
    figure.update_layout(
        title=None,
        legend={
            "title_text": "",
            "orientation": "h",
            "yanchor": "top",
            "y": -0.28,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 12},
            "itemwidth": 30,
            "itemsizing": "constant",
        },
        margin={"l": 55, "r": 25, "t": 35, "b": 110},
    )
    st.plotly_chart(figure, width="stretch")
    st.caption(
        f"Mean paired difference ({first} − {second}): {difference.mean():.8g}; "
        f"median: {difference.median():.8g}; pairs: {len(difference):,}."
    )

st.dataframe(summary, width="stretch", hide_index=True)
if metric.startswith("framework_"):
    st.warning(
        "Own risks are framework-specific conditional quantities and are not interpreted as directly equivalent losses."
    )
render_footer()
