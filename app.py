"""Landing page for the GChSPFAM-GE-3RF research dashboard."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS
from src.metrics import framework_overview
from src.runtime import get_repository
from src.ui import apply_global_filters, render_data_source_badge, render_footer, render_page_header

st.set_page_config(
    page_title="Overview",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_page_header("Overview")

repository = get_repository()
render_data_source_badge(repository)

selected = apply_global_filters(repository.selected_plans())
if selected.empty:
    st.warning("No research records match the active global filters.")
    st.stop()
overview = framework_overview(selected)
matched_units = selected[["scenario_id", "prior_id"]].drop_duplicates()
candidate_records = len(matched_units) * 500

st.header("1. Project Introduction and Industry Application")
st.markdown(
    r"""
This research develops a **Group Chain Sampling Plan (GChSP)** for products whose lifetimes
follow the **Generalized Exponential (GE) distribution**. In simple terms, a sample of items is
tested for a fixed period, failures are counted, and the sampling rule determines whether the
current production lot should be accepted. Information from preceding lots is incorporated
through the chain parameter when exactly one failure is observed.

For every combination of product-life assumptions and sampling-plan settings, the computation
examines integer group counts from 1 to 500. Each risk framework independently selects the
**smallest feasible number of groups, \(g^*\)** whose own consumer risk is no greater than 0.10.
The resulting sample size is \(n^*=r g^*\), where \(r\) is the number of items in each group.

**Industry application.** A manufacturer can use these results when planning a truncated
life test for products such as electronic components, mechanical parts, or other reliability
items. After specifying the desired mean lifetime, test duration, assumed GE shape, group size,
and chain rule, the dashboard helps the user understand:

- how many groups and test items are required;
- the probability that a lot will be accepted at different quality levels;
- the protection provided to consumers against accepting an unsatisfactory lot; and
- the corresponding producer-side rejection risk under each statistical framework.

The dashboard supports evidence-based plan review; it does not replace engineering judgement,
distributional validation, or the organization's regulatory and quality-assurance requirements.
"""
)

metric_columns = st.columns(5)
metric_columns[0].metric("Candidate records", f"{candidate_records:,}")
metric_columns[1].metric("Selected plans", f"{len(selected):,}")
metric_columns[2].metric("Matched units", f"{len(matched_units):,}")
metric_columns[3].metric("Frameworks", "3")
metric_columns[4].metric("Consumer-risk ceiling", "0.10")

st.info(
    "All plans use consumer-risk-only optimization. Producer risks and risk sums are evaluated "
    "after selection; they are never used to choose g*."
)

st.header("2. Three Risk Frameworks Overview")
framework_columns = st.columns(3)
with framework_columns[0]:
    st.markdown(
        """
        **Classical**

        Evaluates producer and consumer risks at two fixed failure probabilities representing
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

st.header("3. How to Use This Dashboard")
st.markdown(
    r"""
1. Use **Global Filters** in the sidebar to restrict the entire dashboard by Beta prior,
   mean-life ratio, termination multiplier, GE shape, group size, or chain parameter. Leaving a
   filter empty includes every available value.
2. Open **Selected Plan Explorer** to review one complete industry sampling plan, including its
   selected \(g^*\), required sample size, risks, OC behavior, and acceptance probabilities.
3. Use **All Candidate Explorer** and **Selected g Explorer** to inspect the candidate group
   counts and see exactly where each framework first satisfies its consumer-risk restriction.
4. Use **OC Explorer** and **Sensitivity Explorer** to study acceptance behavior across
   mean-life ratios and the effects of the design parameters.
5. Use **General Comparison** and **Head-to-Head Comparison** for framework-level comparisons,
   then consult **Chart Gallery** for publication-quality figures.
6. Visit **Phases** for the complete computational explanation and **Downloads** to export
   filtered research-ready data for independent analysis.
"""
)

render_footer()
