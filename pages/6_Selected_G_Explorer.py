"""Candidate-level selected-g inspection and matched-scenario heatmaps."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.constants import FRAMEWORK_COLORS
from src.metrics import first_feasible_groups
from src.runtime import get_repository
from src.ui import apply_global_filters, dataframe_download, render_data_source_badge, render_footer, render_page_header


def gradient_styles(series: pd.Series, light: str, dark: str) -> list[str]:
    """Return dependency-free gradient CSS for one numerical risk column."""
    minimum = float(series.min())
    maximum = float(series.max())
    span = maximum - minimum
    light_rgb = tuple(int(light[index : index + 2], 16) for index in (1, 3, 5))
    dark_rgb = tuple(int(dark[index : index + 2], 16) for index in (1, 3, 5))
    styles = []
    for value in series.astype(float):
        weight = 0.0 if span == 0 else (value - minimum) / span
        rgb = tuple(round(start + weight * (end - start)) for start, end in zip(light_rgb, dark_rgb, strict=True))
        foreground = "#FFFFFF" if weight >= 0.58 else "#17202A"
        styles.append(f"background-color: rgb{rgb}; color: {foreground}")
    return styles


st.set_page_config(page_title="Selected g Explorer", page_icon="🔢", layout="wide")
render_page_header(
    "Selected g Explorer",
    "Inspect all candidate group counts and compare Classical, Average, and Bayesian selected g⁎ across matched scenarios.",
)
repository = get_repository()
render_data_source_badge(repository)

st.subheader("Candidate g selection for one prior–scenario unit")
index = apply_global_filters(repository.scenario_prior_index())
if index.empty:
    st.warning("No prior–scenario units match the active global filters.")
    st.stop()
st.caption(
    "Candidate rows are queried from Neon only after you click Load. "
    "The first request after inactivity may take several seconds; recent traces are cached."
)
with st.form("selected_g_trace_selector"):
    selectors = st.columns(6)
    prior = selectors[0].selectbox("Prior", sorted(index.prior_id.unique()), key="g_prior")
    ratio = selectors[1].selectbox("ρA", sorted(index.acceptable_mean_life_ratio.unique()), key="g_ratio")
    termination = selectors[2].selectbox("a", sorted(index.termination_multiplier.unique()), key="g_termination")
    shape = selectors[3].selectbox("λ", sorted(index.ge_shape.unique()), key="g_shape")
    group_size = selectors[4].selectbox("r", sorted(index.group_size_r.unique()), key="g_group_size")
    chain = selectors[5].selectbox("i", sorted(index.chain_parameter_i.unique()), key="g_chain")
    load_requested = st.form_submit_button("Load selected-g trace", type="primary")

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
    st.session_state["selected_g_trace_selection"] = {
        "scenario_id": str(chosen.iloc[0].scenario_id),
        "prior_id": str(prior),
    }

selection = st.session_state.get("selected_g_trace_selection")
if selection is None:
    st.info("Choose one prior–scenario combination, then click **Load selected-g trace**.")
    render_footer()
    st.stop()

scenario_id = selection["scenario_id"]
loaded_prior = selection["prior_id"]
with st.spinner(f"Loading all 500 candidate group counts for {scenario_id} / {loaded_prior}…"):
    trace = repository.candidate_trace(scenario_id, loaded_prior)
st.caption(f"Loaded prior–scenario unit: {scenario_id} / {loaded_prior}")
selected_g = first_feasible_groups(trace)

risk_columns = {
    "Classical": {"consumer": "cr", "producer": "pr", "sum": "msr"},
    "Average": {"consumer": "acr", "producer": "apr", "sum": "msar"},
    "Bayesian": {"consumer": "bcr", "producer": "bpr", "sum": "msbr"},
}
summary_rows = []
for framework, columns in risk_columns.items():
    g_value = selected_g[framework]
    selected_row = trace.loc[trace["candidate_g"] == g_value].iloc[0] if g_value is not None else None
    summary_rows.append(
        {
            "Framework": framework,
            "Selected g⁎": g_value,
            "Selected n⁎": None if selected_row is None else int(selected_row["candidate_n"]),
            "Own producer risk": None if selected_row is None else float(selected_row[columns["producer"]]),
            "Own consumer risk": None if selected_row is None else float(selected_row[columns["consumer"]]),
            "Own risk sum": None if selected_row is None else float(selected_row[columns["sum"]]),
        }
    )
summary = pd.DataFrame(summary_rows)
st.dataframe(
    summary,
    width="stretch",
    hide_index=True,
    column_config={
        "Own producer risk": st.column_config.NumberColumn(format="%.10f"),
        "Own consumer risk": st.column_config.NumberColumn(format="%.10f"),
        "Own risk sum": st.column_config.NumberColumn(format="%.10f"),
    },
)

st.markdown("#### All candidate g values")
candidate_table = trace[
    [
        "ge_shape",
        "termination_multiplier",
        "acceptable_mean_life_ratio",
        "chain_parameter_i",
        "group_size_r",
        "candidate_g",
        "candidate_n",
        "cr",
        "acr",
        "bcr",
    ]
].rename(
    columns={
        "ge_shape": "λ",
        "termination_multiplier": "a",
        "acceptable_mean_life_ratio": "ρA",
        "chain_parameter_i": "i",
        "group_size_r": "r",
        "candidate_g": "g",
        "candidate_n": "n",
        "cr": "CR",
        "acr": "ACR",
        "bcr": "BCR",
    }
)
candidate_table["Selected g⁎"] = candidate_table["g"].map(
    lambda value: ", ".join(framework for framework, selected in selected_g.items() if selected == value)
)
candidate_range = st.slider(
    "Displayed g range",
    int(candidate_table["g"].min()),
    int(candidate_table["g"].max()),
    (int(candidate_table["g"].min()), int(candidate_table["g"].max())),
    key="selected_g_range",
)
candidate_view = candidate_table[candidate_table["g"].between(*candidate_range)]
styled_candidate_view = (
    candidate_view.style.apply(lambda series: gradient_styles(series, "#EAF2FB", "#17365D"), subset=["CR"])
    .apply(lambda series: gradient_styles(series, "#EAF6EF", "#2E7D5B"), subset=["ACR"])
    .apply(lambda series: gradient_styles(series, "#FFF7D6", "#C69200"), subset=["BCR"])
)
st.dataframe(
    styled_candidate_view,
    width="stretch",
    height=600,
    hide_index=True,
    column_config={
        "CR": st.column_config.NumberColumn(format="%.10f"),
        "ACR": st.column_config.NumberColumn(format="%.10f"),
        "BCR": st.column_config.NumberColumn(format="%.10f"),
    },
)
st.caption("Risk gradients: CR uses blue, ACR uses green, and BCR uses gold; darker cells indicate larger values.")
st.caption(
    "CR, ACR, and BCR retain their distinct conditioning definitions. Each selected g⁎ is the first row where its own consumer risk is at most 0.10."
)
dataframe_download(
    candidate_view,
    f"selected_g_candidates_{scenario_id}_{loaded_prior}.csv",
    "Download displayed g table",
)

st.divider()
st.subheader("Matched-scenario selected g⁎ heatmaps")
st.write(
    "Choose a prior, GE shape, and GChSP design. The three heatmaps use the same scale, so cell colors are directly comparable across frameworks."
)
matched = apply_global_filters(repository.matched_results())
designs = (
    matched[["group_size_r", "chain_parameter_i"]].drop_duplicates().sort_values(["group_size_r", "chain_parameter_i"])
)
design_options = [f"r={int(row.group_size_r)}, i={int(row.chain_parameter_i)}" for row in designs.itertuples()]
heatmap_controls = st.columns(3)
heatmap_prior = heatmap_controls[0].selectbox("Heatmap prior", sorted(matched.prior_id.unique()))
heatmap_shape = heatmap_controls[1].selectbox("Heatmap GE shape λ", sorted(matched.ge_shape.unique()))
heatmap_design = heatmap_controls[2].selectbox("Heatmap GChSP design", design_options)
design_position = design_options.index(heatmap_design)
heatmap_r = int(designs.iloc[design_position].group_size_r)
heatmap_i = int(designs.iloc[design_position].chain_parameter_i)

heatmap_scope = matched[
    (matched["prior_id"] == heatmap_prior)
    & (matched["ge_shape"] == heatmap_shape)
    & (matched["group_size_r"] == heatmap_r)
    & (matched["chain_parameter_i"] == heatmap_i)
].copy()
heatmap_columns = {
    "Classical": "classical_selected_g",
    "Average": "average_selected_g",
    "Bayesian": "bayesian_selected_g",
}
all_heatmap_values = heatmap_scope[list(heatmap_columns.values())].to_numpy(dtype=float)
color_min = float(all_heatmap_values.min())
color_max = float(all_heatmap_values.max())
if color_min == color_max:
    color_max = color_min + 1.0

heatmap_panels = st.columns(3)
for panel, (framework, value_column) in zip(heatmap_panels, heatmap_columns.items(), strict=True):
    matrix = heatmap_scope.pivot(
        index="termination_multiplier",
        columns="acceptable_mean_life_ratio",
        values=value_column,
    ).sort_index(ascending=False)
    heatmap = px.imshow(
        matrix,
        text_auto=".0f",
        aspect="auto",
        color_continuous_scale=[[0.0, "#F3F6F9"], [1.0, FRAMEWORK_COLORS[framework]]],
        range_color=(color_min, color_max),
        labels={"x": "ρA", "y": "Termination multiplier a", "color": "g⁎"},
    )
    heatmap.update_layout(
        title={"text": f"{framework} selected g⁎", "x": 0.5, "xanchor": "center"},
        margin={"l": 25, "r": 10, "t": 55, "b": 35},
        coloraxis_colorbar={"title": "g⁎", "thickness": 10},
    )
    with panel:
        st.plotly_chart(heatmap, width="stretch")

heatmap_table = heatmap_scope[
    [
        "scenario_id",
        "prior_id",
        "ge_shape",
        "termination_multiplier",
        "acceptable_mean_life_ratio",
        "group_size_r",
        "chain_parameter_i",
        "classical_selected_g",
        "average_selected_g",
        "bayesian_selected_g",
    ]
].rename(
    columns={
        "ge_shape": "λ",
        "termination_multiplier": "a",
        "acceptable_mean_life_ratio": "ρA",
        "group_size_r": "r",
        "chain_parameter_i": "i",
        "classical_selected_g": "Classical g⁎",
        "average_selected_g": "Average g⁎",
        "bayesian_selected_g": "Bayesian g⁎",
    }
)
heatmap_table = heatmap_table.sort_values(["a", "ρA"], kind="stable")
with st.expander("View the 48 matched scenarios represented by these heatmaps"):
    st.dataframe(heatmap_table, width="stretch", hide_index=True)
    dataframe_download(
        heatmap_table,
        f"selected_g_heatmap_{heatmap_prior}_lambda{heatmap_shape}_r{heatmap_r}_i{heatmap_i}.csv",
        "Download heatmap scenario table",
    )

render_footer()
