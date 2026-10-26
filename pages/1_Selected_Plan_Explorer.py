"""Interactive selected-plan exploration."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS, RISK_LABELS
from src.runtime import get_repository
from src.ui import dataframe_download, render_data_source_badge, render_footer, render_page_header, sidebar_filters

st.set_page_config(page_title="Selected Plan Explorer", page_icon="🔎", layout="wide")
render_page_header(
    "Selected Plan Explorer",
    "Inspect selected g*, sample size, all six risks, and all three risk sums at every framework-selected plan.",
)

repository = get_repository()
render_data_source_badge(repository)
filters = sidebar_filters(repository.filter_options())
data = repository.selected_plans(filters)

if data.empty:
    st.warning("No selected plans match the current filters.")
    st.stop()

metrics = st.columns(5)
metrics[0].metric("Records", f"{len(data):,}")
metrics[1].metric("Mean g*", f"{data['selected_g'].mean():.3f}")
metrics[2].metric("Median g*", f"{data['selected_g'].median():.3f}")
metrics[3].metric("Mean n*", f"{data['selected_n'].mean():.3f}")
metrics[4].metric("Mean L(p₁)", f"{data['l_p1'].mean():.6f}")

left, right = st.columns(2)
with left:
    figure = px.box(
        data,
        x="framework",
        y="selected_g",
        color="framework",
        color_discrete_map=FRAMEWORK_COLORS,
        points=False,
        category_orders={"framework": list(FRAMEWORK_COLORS)},
        labels={"framework": "Framework", "selected_g": "Selected g*"},
    )
    st.plotly_chart(apply_academic_layout(figure, "Distribution of selected g*"), width="stretch")
with right:
    summary = (
        data.groupby("framework", observed=True)[
            ["framework_producer_risk", "framework_consumer_risk", "framework_risk_sum"]
        ]
        .mean()
        .reset_index()
        .melt(id_vars="framework", var_name="measure", value_name="mean")
    )
    measure_labels = {
        "framework_producer_risk": "Own producer risk",
        "framework_consumer_risk": "Own consumer risk",
        "framework_risk_sum": "Own risk sum",
    }
    summary["measure"] = summary["measure"].map(measure_labels)
    figure = px.bar(
        summary,
        x="framework",
        y="mean",
        color="measure",
        barmode="group",
        labels={"framework": "Framework", "mean": "Mean risk", "measure": "Measure"},
    )
    st.plotly_chart(apply_academic_layout(figure, "Framework-specific own risks"), width="stretch")

st.subheader("Matched scenario detail")
keys = data[["scenario_id", "prior_id"]].drop_duplicates().sort_values(["scenario_id", "prior_id"])
labels = (keys["scenario_id"] + " · " + keys["prior_id"]).tolist()
chosen = st.selectbox("Scenario and prior", labels)
scenario_id, prior_id = chosen.split(" · ", maxsplit=1)
detail = data[(data.scenario_id == scenario_id) & (data.prior_id == prior_id)].copy()

risk_columns = ["pr", "apr", "bpr", "cr", "acr", "bcr"]
risk_long = detail.melt(
    id_vars=["framework", "selected_g", "selected_n"],
    value_vars=risk_columns,
    var_name="risk",
    value_name="value",
)
risk_long["risk"] = risk_long["risk"].map(RISK_LABELS)
figure = px.bar(
    risk_long,
    x="risk",
    y="value",
    color="framework",
    barmode="group",
    color_discrete_map=FRAMEWORK_COLORS,
    labels={"risk": "Risk evaluated at the selected plan", "value": "Risk", "framework": "Selected by"},
)
st.plotly_chart(apply_academic_layout(figure, f"All six risks at {scenario_id} / {prior_id}"), width="stretch")

display_columns = [
    "scenario_id",
    "prior_id",
    "framework",
    "selected_g",
    "selected_n",
    "l_p1",
    "l_p2",
    "pr",
    "apr",
    "bpr",
    "cr",
    "acr",
    "bcr",
    "msr",
    "msar",
    "msbr",
    "framework_producer_risk",
    "framework_consumer_risk",
    "framework_risk_sum",
    "consumer_risk_margin",
    "numerical_validation_status",
]
st.dataframe(detail[display_columns], width="stretch", hide_index=True)
st.warning(
    "PR, APR, and BPR—and likewise CR, ACR, and BCR—use different conditioning and denominators. "
    "Own-risk comparisons are descriptive and are not treated as mathematically equivalent risks."
)

dataframe_download(data, "selected_plans_filtered.csv")
render_footer()
