"""Fixed-plan acceptance-probability exploration."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS
from src.oc import gchsp_acceptance_probability
from src.runtime import get_repository
from src.ui import apply_global_filters, render_data_source_badge, render_footer, render_page_header

st.set_page_config(page_title="L(p) Explorer", page_icon="📈", layout="wide")
render_page_header(
    "L(p) Explorer",
    "Hold the consumer-risk-selected plan fixed while evaluating acceptance across mean-life ratios.",
)
repository = get_repository()
render_data_source_badge(repository)
data = apply_global_filters(repository.fixed_plan_oc(), mean_ratio_column="evaluation_mean_life_ratio")
if data.empty:
    st.warning("No OC records match the active global filters.")
    st.stop()

selectors = st.columns(5)
prior = selectors[0].selectbox("Beta prior", sorted(data.prior_id.unique()))
shape = selectors[1].selectbox("GE shape λ", sorted(data.ge_shape.unique()))
termination = selectors[2].selectbox("Termination a", sorted(data.termination_multiplier.unique()))
group_size = selectors[3].selectbox("Group size r", sorted(data.group_size_r.unique()))
chain = selectors[4].selectbox("Chain i", sorted(data.chain_parameter_i.unique()))

subset = data[
    (data.prior_id == prior)
    & (data.ge_shape == shape)
    & (data.termination_multiplier == termination)
    & (data.group_size_r == group_size)
    & (data.chain_parameter_i == chain)
].copy()

figure = px.line(
    subset,
    x="evaluation_mean_life_ratio",
    y="l_p",
    color="framework",
    markers=True,
    color_discrete_map=FRAMEWORK_COLORS,
    category_orders={"framework": list(FRAMEWORK_COLORS)},
    hover_data=["selected_g", "selected_n", "failure_probability_p"],
    labels={
        "evaluation_mean_life_ratio": "Evaluation mean-life ratio ρ",
        "l_p": "Acceptance probability L(p)",
        "framework": "Selected by",
    },
)
st.plotly_chart(
    apply_academic_layout(figure, "Fixed-plan acceptance probability across mean-life ratios"), width="stretch"
)

plan_table = subset[["framework", "selected_g", "selected_n", "consumer_risk_limit"]].drop_duplicates()
st.dataframe(plan_table, width="stretch", hide_index=True)

p_grid = np.linspace(0.0, 1.0, 501)
curve_frames = []
for plan in plan_table.itertuples(index=False):
    curve_frames.append(
        pd.DataFrame(
            {
                "failure_probability_p": p_grid,
                "l_p": gchsp_acceptance_probability(
                    p_grid,
                    g=int(plan.selected_g),
                    r=int(group_size),
                    i=int(chain),
                ),
                "framework": plan.framework,
                "selected_g": int(plan.selected_g),
            }
        )
    )
oc_curves = pd.concat(curve_frames, ignore_index=True)
oc_figure = px.line(
    oc_curves,
    x="failure_probability_p",
    y="l_p",
    color="framework",
    color_discrete_map=FRAMEWORK_COLORS,
    category_orders={"framework": list(FRAMEWORK_COLORS)},
    hover_data={"selected_g": True, "failure_probability_p": ":.4f", "l_p": ":.6f"},
    labels={
        "failure_probability_p": "Failure probability p",
        "l_p": "Acceptance probability L(p)",
        "framework": "Selected by",
        "selected_g": "Selected g*",
    },
)
oc_figure.update_yaxes(range=[0.0, 1.01])
st.plotly_chart(apply_academic_layout(oc_figure, "OC curves: L(p) versus p"), width="stretch")

st.info(
    "The plotted g⁎ is fixed across evaluation ratios. Consumer-risk selection depends on p₂=p(1; a, λ), "
    "not on the acceptable design ratio ρA. The evaluation ratio changes p and L(p), not the selected group count."
)
render_footer()
