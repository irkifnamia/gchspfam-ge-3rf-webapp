"""Three-framework head-to-head comparisons for g* and fixed-plan L(p)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS, FRAMEWORKS
from src.metrics import WINNER_CATEGORY_ORDER, framework_win_percentages
from src.runtime import get_repository
from src.ui import dataframe_download, render_data_source_badge, render_footer, render_page_header

WINNER_COLORS = {
    "Bayesian win": "#C9A227",
    "Average win": "#4C78A8",
    "Classical win": "#17365D",
    "Bayesian & Average tie": "#8E7CC3",
    "Bayesian & Classical tie": "#6AA84F",
    "Average & Classical tie": "#76A5AF",
    "Three-way tie": "#B7B7B7",
}


def filter_values(frame: pd.DataFrame, selections: dict[str, list[object]]) -> pd.DataFrame:
    """Apply inclusive multi-value filters without changing the source frame."""
    result = frame
    for column, values in selections.items():
        result = result[result[column].isin(values)]
    return result.copy()


def complete_feasible_keys(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Return keys having feasible records for all three frameworks."""
    eligible = (
        frame.groupby(keys, observed=True)
        .agg(frameworks=("framework", "nunique"), all_feasible=("feasible", "all"))
        .reset_index()
    )
    return eligible[(eligible["frameworks"] == len(FRAMEWORKS)) & eligible["all_feasible"]][keys]


def winner_bar(data: pd.DataFrame, title: str) -> None:
    """Render a one-row 100% stacked outcome bar."""
    chart_data = data.copy()
    chart_data["comparison"] = "All complete trios"
    figure = px.bar(
        chart_data,
        x="percentage",
        y="comparison",
        color="outcome",
        orientation="h",
        color_discrete_map=WINNER_COLORS,
        category_orders={"outcome": list(WINNER_CATEGORY_ORDER)},
        text=chart_data["percentage"].map(lambda value: f"{value:.1f}%" if value >= 4.0 else ""),
        labels={"percentage": "Percentage", "comparison": "", "outcome": "Outcome"},
    )
    figure.update_layout(barmode="stack", xaxis_range=[0, 100])
    st.plotly_chart(apply_academic_layout(figure, title), width="stretch")


st.set_page_config(page_title="Head-to-Head Comparison", page_icon="🥇", layout="wide")
render_page_header(
    "Head-to-Head Comparison",
    "Compare selected g* and fixed-plan acceptance probability across Classical, Average, and Bayesian frameworks.",
)
repository = get_repository()
render_data_source_badge(repository)

version = st.radio(
    "Comparison version",
    ["Matched feasible", "All available (not feasibility-matched)"],
    horizontal=True,
    help=(
        "Matched feasible retains only prior–scenario units with feasible results for all three frameworks. "
        "The all-available version retains every framework record; winner shares still require a complete trio."
    ),
)
matched_version = version == "Matched feasible"

selected = repository.selected_plans()
oc = repository.fixed_plan_oc()
with st.expander("Comparison filters", expanded=False):
    filter_columns = st.columns(5)
    priors = filter_columns[0].multiselect(
        "Beta priors", sorted(selected["prior_id"].unique()), default=sorted(selected["prior_id"].unique())
    )
    shapes = filter_columns[1].multiselect(
        "GE shapes λ", sorted(selected["ge_shape"].unique()), default=sorted(selected["ge_shape"].unique())
    )
    terminations = filter_columns[2].multiselect(
        "Termination a",
        sorted(selected["termination_multiplier"].unique()),
        default=sorted(selected["termination_multiplier"].unique()),
    )
    group_sizes = filter_columns[3].multiselect(
        "Group size r", sorted(selected["group_size_r"].unique()), default=sorted(selected["group_size_r"].unique())
    )
    chains = filter_columns[4].multiselect(
        "Chain i",
        sorted(selected["chain_parameter_i"].unique()),
        default=sorted(selected["chain_parameter_i"].unique()),
    )

selections = {
    "prior_id": priors,
    "ge_shape": shapes,
    "termination_multiplier": terminations,
    "group_size_r": group_sizes,
    "chain_parameter_i": chains,
}
selected = filter_values(selected, selections)
oc = filter_values(oc, selections)
if selected.empty or oc.empty:
    st.warning("The current filters leave no records to compare.")
    st.stop()

st.caption(
    "For selected g*, smaller is the winning outcome. For L(p) at an evaluated mean-life ratio, larger acceptance "
    "probability is the winning outcome. Exact g ties and numerical L(p) ties within 5×10⁻¹² are retained."
)

st.subheader("1. Selected g* comparison across scenarios")
g_keys = ["scenario_id", "prior_id"]
if matched_version:
    eligible_g = complete_feasible_keys(selected, g_keys)
    selected_comparison = selected.merge(eligible_g, on=g_keys, how="inner")
else:
    selected_comparison = selected

g_pivot = selected_comparison.pivot_table(
    index=g_keys,
    columns="framework",
    values="selected_g",
    aggfunc="first",
).reindex(columns=FRAMEWORKS)
g_complete = g_pivot.dropna()
g_winners = framework_win_percentages(g_complete, higher_is_better=False, tolerance=0.0)
g_incomplete = len(g_pivot) - len(g_complete)

g_summary = (
    selected_comparison.groupby("framework", observed=True)["selected_g"]
    .agg(records="count", mean="mean", median="median", minimum="min", maximum="max")
    .reindex(FRAMEWORKS)
    .reset_index()
)
metrics = st.columns(4)
metrics[0].metric("Selected-plan records", f"{len(selected_comparison):,}")
metrics[1].metric("Complete framework trios", f"{len(g_complete):,}")
metrics[2].metric("Incomplete trios excluded", f"{g_incomplete:,}")
metrics[3].metric("All-three feasible", "Yes" if g_incomplete == 0 else "No")

g_frequency = (
    selected_comparison.dropna(subset=["selected_g"])
    .groupby(["framework", "selected_g"], observed=True)
    .size()
    .reset_index(name="count")
)
g_frequency["percentage"] = 100.0 * g_frequency["count"] / g_frequency.groupby("framework")["count"].transform("sum")
left, right = st.columns([1.15, 1])
with left:
    figure = px.bar(
        g_frequency,
        x="selected_g",
        y="percentage",
        color="framework",
        barmode="group",
        color_discrete_map=FRAMEWORK_COLORS,
        category_orders={"framework": list(FRAMEWORKS)},
        labels={"selected_g": "Selected g*", "percentage": "Within-framework percentage", "framework": "Framework"},
    )
    st.plotly_chart(apply_academic_layout(figure, "Distribution of selected g*"), width="stretch")
with right:
    winner_bar(g_winners, "Selected g* head-to-head outcomes")

summary_tab, outcome_tab = st.tabs(["Framework summary", "Win and tie percentages"])
with summary_tab:
    st.dataframe(g_summary, width="stretch", hide_index=True)
with outcome_tab:
    st.dataframe(
        g_winners,
        width="stretch",
        hide_index=True,
        column_config={"percentage": st.column_config.NumberColumn(format="%.6f%%")},
    )

st.subheader("2. L(p) comparison across mean-life ratios")
lp_keys = [
    "prior_id",
    "ge_shape",
    "termination_multiplier",
    "group_size_r",
    "chain_parameter_i",
    "evaluation_mean_life_ratio",
]
if matched_version:
    eligible_lp = complete_feasible_keys(oc, lp_keys)
    oc_comparison = oc.merge(eligible_lp, on=lp_keys, how="inner")
else:
    oc_comparison = oc

lp_statistic = st.radio("L(p) summary line", ["Mean", "Median"], horizontal=True)
lp_summary = (
    oc_comparison.groupby(["evaluation_mean_life_ratio", "framework"], observed=True)["l_p"]
    .agg(records="count", mean="mean", median="median")
    .reset_index()
)
statistic_column = lp_statistic.lower()
figure = px.line(
    lp_summary,
    x="evaluation_mean_life_ratio",
    y=statistic_column,
    color="framework",
    markers=True,
    color_discrete_map=FRAMEWORK_COLORS,
    category_orders={"framework": list(FRAMEWORKS)},
    hover_data=["records", "mean", "median"],
    labels={
        "evaluation_mean_life_ratio": "Evaluation mean-life ratio ρ",
        statistic_column: f"{lp_statistic} L(p)",
        "framework": "Selected by",
    },
)
st.plotly_chart(
    apply_academic_layout(figure, f"{lp_statistic} fixed-plan acceptance probability across mean-life ratios"),
    width="stretch",
)

lp_pivot = oc_comparison.pivot_table(
    index=lp_keys,
    columns="framework",
    values="l_p",
    aggfunc="first",
).reindex(columns=FRAMEWORKS)
lp_complete = lp_pivot.dropna()
lp_winners_overall = framework_win_percentages(lp_complete, higher_is_better=True, tolerance=5e-12)
lp_by_ratio = []
for ratio_value, ratio_frame in lp_complete.reset_index().groupby("evaluation_mean_life_ratio", observed=True):
    ratio_winners = framework_win_percentages(ratio_frame, higher_is_better=True, tolerance=5e-12)
    ratio_winners["evaluation_mean_life_ratio"] = ratio_value
    lp_by_ratio.append(ratio_winners)
lp_ratio_winners = pd.concat(lp_by_ratio, ignore_index=True)

figure = px.bar(
    lp_ratio_winners,
    x="evaluation_mean_life_ratio",
    y="percentage",
    color="outcome",
    barmode="stack",
    color_discrete_map=WINNER_COLORS,
    category_orders={"outcome": list(WINNER_CATEGORY_ORDER)},
    labels={
        "evaluation_mean_life_ratio": "Evaluation mean-life ratio ρ",
        "percentage": "Percentage of complete trios",
        "outcome": "Outcome",
    },
)
figure.update_yaxes(range=[0, 100])
st.plotly_chart(apply_academic_layout(figure, "L(p) wins and ties by mean-life ratio"), width="stretch")

lp_left, lp_right = st.columns(2)
with lp_left:
    st.markdown("#### Overall L(p) outcomes")
    st.dataframe(
        lp_winners_overall,
        width="stretch",
        hide_index=True,
        column_config={"percentage": st.column_config.NumberColumn(format="%.6f%%")},
    )
with lp_right:
    st.markdown("#### Comparison coverage")
    st.metric("Complete L(p) trios", f"{len(lp_complete):,}")
    st.metric("Incomplete trios excluded", f"{len(lp_pivot) - len(lp_complete):,}")

with st.expander("Download comparison tables"):
    dataframe_download(g_winners, "head_to_head_selected_g_outcomes.csv", "Download selected-g outcomes")
    dataframe_download(lp_summary, "head_to_head_lp_by_ratio.csv", "Download L(p) ratio summary")
    dataframe_download(lp_ratio_winners, "head_to_head_lp_outcomes_by_ratio.csv", "Download L(p) outcomes")

if version == "All available (not feasibility-matched)" and g_incomplete == 0 and len(lp_pivot) == len(lp_complete):
    st.info(
        "All Stage 6 selections are feasible and every comparison key contains all three frameworks. Therefore, the "
        "current all-available and matched-feasible numerical results coincide; the version control is retained for "
        "future datasets that may contain infeasible or incomplete records."
    )

render_footer()
