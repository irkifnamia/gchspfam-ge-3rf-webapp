"""Industry-oriented review of one validated framework-selected sampling plan."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS, FRAMEWORKS
from src.runtime import get_repository
from src.ui import dataframe_download, render_page_header

st.set_page_config(page_title="Selected Plan Explorer", page_icon="🔎", layout="wide")
render_page_header(
    "Selected Plan Explorer",
    "Review one validated sampling plan, its operating instructions, risk performance, and acceptance behavior.",
)

repository = get_repository()
selected = repository.selected_plans()
fixed_oc = repository.fixed_plan_oc()

st.subheader("Choose one sampling plan")
with st.form("industry_plan_selector"):
    first_row = st.columns(4)
    framework = first_row[0].selectbox("Risk framework", list(FRAMEWORKS))
    prior_id = first_row[1].selectbox("Beta prior", sorted(selected["prior_id"].unique()))
    ratio = first_row[2].selectbox(
        "Acceptable mean-life ratio ρA", sorted(selected["acceptable_mean_life_ratio"].unique())
    )
    termination = first_row[3].selectbox(
        "Termination multiplier a", sorted(selected["termination_multiplier"].unique())
    )
    second_row = st.columns(3)
    shape = second_row[0].selectbox("GE shape λ", sorted(selected["ge_shape"].unique()))
    group_size = second_row[1].selectbox("Items per group r", sorted(selected["group_size_r"].unique()))
    chain = second_row[2].selectbox("Preceding lots i", sorted(selected["chain_parameter_i"].unique()))
    apply_plan = st.form_submit_button("Review this sampling plan", type="primary")

form_selection = {
    "framework": framework,
    "prior_id": prior_id,
    "acceptable_mean_life_ratio": ratio,
    "termination_multiplier": termination,
    "ge_shape": shape,
    "group_size_r": group_size,
    "chain_parameter_i": chain,
}
if apply_plan or "industry_plan_selection" not in st.session_state:
    st.session_state["industry_plan_selection"] = form_selection
selection = st.session_state["industry_plan_selection"]

plan_rows = selected.copy()
for column, value in selection.items():
    plan_rows = plan_rows[plan_rows[column] == value]
if len(plan_rows) != 1:
    st.error(f"Expected one selected plan for this specification; found {len(plan_rows):,}.")
    st.stop()
plan = plan_rows.iloc[0]

framework = str(plan["framework"])
selected_g = int(plan["selected_g"])
selected_n = int(plan["selected_n"])
r = int(plan["group_size_r"])
i = int(plan["chain_parameter_i"])
a = float(plan["termination_multiplier"])

own_columns = {
    "Classical": ("pr", "cr", "msr", "PR", "CR", "MSR"),
    "Average": ("apr", "acr", "msar", "APR", "ACR", "MSAR"),
    "Bayesian": ("bpr", "bcr", "msbr", "BPR", "BCR", "MSBR"),
}
producer_column, consumer_column, sum_column, producer_label, consumer_label, sum_label = own_columns[framework]

st.subheader("Selected plan at a glance")
metrics = st.columns(6)
metrics[0].metric("Framework", framework)
metrics[1].metric("Selected groups g*", f"{selected_g}")
metrics[2].metric("Items per group r", f"{r}")
metrics[3].metric("Required sample n*", f"{selected_n}")
metrics[4].metric(f"Own consumer risk ({consumer_label})", f"{float(plan[consumer_column]):.6f}")
metrics[5].metric("Consumer-risk margin", f"{float(plan['consumer_risk_margin']):.6f}")

left, right = st.columns([1.2, 1])
with left:
    st.markdown("#### Operating instructions")
    st.markdown(
        rf"""
1. Arrange **{selected_n} test items** into **{selected_g} groups**, with **{r} items per group**.
2. Terminate each lifetime test at **$t_0={a:g}\,\mu_0$**.
3. Count the number of failures, $d$, observed before $t_0$.
4. **Accept the current lot when $d=0$.**
5. When $d=1$, accept only if no failures were found in the preceding **{i} lot(s)**; otherwise reject.
6. Reject the current lot when $d>1$.
"""
    )
    if framework == "Classical":
        st.info("The Classical selected plan is independent of the displayed Beta prior.")
with right:
    plan_matrix = pd.DataFrame(
        [
            ("Scenario", plan["scenario_id"], "Validated experimental scenario"),
            ("Prior", plan["prior_id"], "Used by Average and Bayesian risks"),
            ("Framework", framework, "Consumer-risk restriction used for g*"),
            ("GE shape λ", f"{float(plan['ge_shape']):g}", "Lifetime-distribution shape"),
            ("Mean-life ratio ρA", f"{float(plan['acceptable_mean_life_ratio']):g}", "Acceptable quality point"),
            ("Termination a", f"{a:g}", "Test time multiplier in t₀=aμ₀"),
            ("Plan (g*, r, i)", f"({selected_g}, {r}, {i})", "Groups, items/group, preceding lots"),
            ("Sample size n*", f"{selected_n}", "n*=r×g*"),
            ("p₁", f"{float(plan['p1']):.10f}", "Failure probability at acceptable quality"),
            ("p₂", f"{float(plan['p2']):.10f}", "Failure probability at limiting quality"),
        ],
        columns=["Plan element", "Selected value", "Operational meaning"],
    )
    st.markdown("#### Plan specification matrix")
    st.dataframe(plan_matrix, width="stretch", hide_index=True)

st.subheader("Plan risk profile")
risk_profile = pd.DataFrame(
    {
        "Measure": [f"Own producer risk ({producer_label})", f"Own consumer risk ({consumer_label})", sum_label],
        "Value": [float(plan[producer_column]), float(plan[consumer_column]), float(plan[sum_column])],
    }
)
risk_figure = px.bar(
    risk_profile,
    x="Value",
    y="Measure",
    orientation="h",
    text_auto=".6f",
    color="Measure",
    color_discrete_sequence=[FRAMEWORK_COLORS[framework], "#C9A227", "#8090A0"],
)
risk_figure.update_layout(showlegend=False)
st.plotly_chart(apply_academic_layout(risk_figure, f"{framework} framework risk measures"), width="stretch")
st.caption(
    f"Only {consumer_label}≤0.10 selected g*. {producer_label} and {sum_label} are performance measures and did not constrain selection."
)

oc_scope = fixed_oc[
    (fixed_oc["prior_id"] == plan["prior_id"])
    & (fixed_oc["ge_shape"] == plan["ge_shape"])
    & (fixed_oc["termination_multiplier"] == plan["termination_multiplier"])
    & (fixed_oc["group_size_r"] == plan["group_size_r"])
    & (fixed_oc["chain_parameter_i"] == plan["chain_parameter_i"])
    & (fixed_oc["framework"] == framework)
].sort_values("evaluation_mean_life_ratio", kind="stable")

if oc_scope.empty:
    st.warning("No fixed-plan OC evaluations were found for this plan.")
else:
    st.subheader("Operating characteristic across mean-life ratios")
    chart, matrix_panel = st.columns([1.45, 1])
    with chart:
        oc_figure = px.line(
            oc_scope,
            x="evaluation_mean_life_ratio",
            y="l_p",
            markers=True,
            color_discrete_sequence=[FRAMEWORK_COLORS[framework]],
            hover_data={"failure_probability_p": ":.10f", "selected_g": True, "selected_n": True},
            labels={
                "evaluation_mean_life_ratio": "Mean-life ratio ρ",
                "l_p": "Acceptance probability L(p)",
            },
        )
        oc_figure.update_yaxes(range=[0, 1])
        oc_figure.add_vline(
            x=float(plan["acceptable_mean_life_ratio"]),
            line_dash="dot",
            line_color="#A33A3A",
            annotation_text="Design ρA",
        )
        st.plotly_chart(
            apply_academic_layout(oc_figure, "Fixed selected plan: L(p) across mean-life ratios"),
            width="stretch",
        )
    with matrix_panel:
        heatmap_matrix = oc_scope.pivot_table(
            index="framework",
            columns="evaluation_mean_life_ratio",
            values="l_p",
            aggfunc="first",
        )
        heatmap = px.imshow(
            heatmap_matrix,
            text_auto=".4f",
            aspect="auto",
            range_color=(0, 1),
            color_continuous_scale="Blues",
            labels={"x": "Mean-life ratio ρ", "y": "", "color": "L(p)"},
        )
        heatmap.update_layout(margin={"l": 20, "r": 15, "t": 45, "b": 30})
        st.plotly_chart(heatmap, width="stretch")

    oc_matrix = oc_scope[
        [
            "evaluation_mean_life_ratio",
            "failure_probability_p",
            "selected_g",
            "selected_n",
            "l_p",
        ]
    ].rename(
        columns={
            "evaluation_mean_life_ratio": "Mean-life ratio ρ",
            "failure_probability_p": "Failure probability p",
            "selected_g": "Selected g*",
            "selected_n": "Sample size n*",
            "l_p": "Acceptance probability L(p)",
        }
    )
    st.markdown("#### OC decision matrix")
    st.dataframe(
        oc_matrix,
        width="stretch",
        hide_index=True,
        column_config={
            "Failure probability p": st.column_config.NumberColumn(format="%.10f"),
            "Acceptance probability L(p)": st.column_config.NumberColumn(format="%.10f"),
        },
    )

with st.expander("Research risk details for this selected plan"):
    risk_details = pd.DataFrame(
        {
            "Measure": ["PR", "APR", "BPR", "CR", "ACR", "BCR", "MSR", "MSAR", "MSBR", "L(p₁)", "L(p₂)"],
            "Value": [
                plan["pr"],
                plan["apr"],
                plan["bpr"],
                plan["cr"],
                plan["acr"],
                plan["bcr"],
                plan["msr"],
                plan["msar"],
                plan["msbr"],
                plan["l_p1"],
                plan["l_p2"],
            ],
        }
    )
    st.dataframe(
        risk_details,
        width="stretch",
        hide_index=True,
        column_config={"Value": st.column_config.NumberColumn(format="%.12f")},
    )

st.subheader("Download this plan")
download_left, download_right = st.columns(2)
with download_left:
    dataframe_download(
        plan_rows,
        f"selected_plan_{plan['scenario_id']}_{plan['prior_id']}_{framework}.csv",
        "Download plan record",
    )
with download_right:
    if not oc_scope.empty:
        dataframe_download(
            oc_scope,
            f"selected_plan_oc_{plan['scenario_id']}_{plan['prior_id']}_{framework}.csv",
            "Download plan OC evaluations",
        )
