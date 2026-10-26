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

# Pass an explicit empty subtitle so rolling Streamlit deployments remain
# compatible with both the previous and current shared-header signatures.
render_page_header("Overview", "")

repository = get_repository()
render_data_source_badge(repository)

selected = apply_global_filters(repository.selected_plans())
if selected.empty:
    st.warning("No research records match the active global filters.")
    st.stop()
overview = framework_overview(selected)
matched_units = selected[["scenario_id", "prior_id"]].drop_duplicates()
candidate_records = len(matched_units) * 500

st.header("1. Project Introduction")
st.markdown(
    """
This project develops a **Group Chain Sampling Plan (GChSP)** for products whose lifetimes
follow the **Generalized Exponential (GE) distribution**. A sample is tested for a fixed time,
the number of failures is observed, and the current production lot is accepted or rejected.
When exactly one failure occurs, the outcomes of preceding lots are used through the chain
parameter.

The corrected GE model converts a mean-life ratio into a failure probability. That probability
is then evaluated with the complete GChSP operating-characteristic function:
"""
)

formula_columns = st.columns(2)
with formula_columns[0]:
    st.caption("Corrected GE failure probability")
    st.latex(r"p(\rho;a,\lambda)=\left[1-\exp\left(-\frac{aH_\lambda}{\rho}\right)\right]^\lambda")
    st.latex(r"H_\lambda=\psi(\lambda+1)-\psi(1)")
with formula_columns[1]:
    st.caption("GChSP operating-characteristic function")
    st.latex(r"L_g(p)=(1-p)^{gr}+gr\,p(1-p)^{gr(i+1)-1}")

st.markdown(
    "For each framework, the computation searches the integer group counts from 1 through 500 "
    "and selects the first group count satisfying that framework's consumer-risk restriction:"
)
st.latex(r"g_F^*=\min\left\{g\in\{1,\ldots,500\}:R_F(g)\leq0.10\right\},\quad n_F^*=r g_F^*,\quad F\in\{C,A,B\}")
st.markdown(
    r"Here, $R_C=CR$, $R_A=ACR$, and $R_B=BCR$. Producer risks and risk sums are calculated "
    r"after $g_F^*$ is selected; they do not influence the optimization."
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

st.header("2. Industry Application")
st.markdown(
    """
The findings can support routine acceptance decisions for products tested in groups under a
truncated life test. The following flow translates the research results into a practical sequence.
"""
)
st.markdown(
    """
    <style>
      .industry-flow {
        display: flex;
        flex-direction: column;
        gap: 0.32rem;
        margin: 0.8rem 0 1.2rem;
      }
      .industry-step {
        align-items: flex-start;
        background: #F5F7FA;
        border: 1px solid #D5DBE3;
        border-left: 6px solid #17365D;
        border-radius: 0.55rem;
        display: grid;
        gap: 0.75rem;
        grid-template-columns: 2.4rem 1fr;
        padding: 0.78rem 0.95rem;
      }
      .industry-step.decision { border-left-color: #C9A227; background: #FFF9E8; }
      .industry-number {
        align-items: center;
        background: #17365D;
        border-radius: 50%;
        color: white;
        display: flex;
        font-weight: 800;
        height: 2.15rem;
        justify-content: center;
        width: 2.15rem;
      }
      .industry-step.decision .industry-number { background: #A47E10; }
      .industry-step strong { color: #17365D; font-size: 1.02rem; }
      .industry-arrow { color: #7B8794; font-size: 1.25rem; line-height: 1; text-align: center; }
    </style>
    <div class="industry-flow">
      <div class="industry-step"><div class="industry-number">1</div><div><strong>Receive and identify the production lot</strong><br>Confirm the product, lot identity, specified mean lifetime, test facilities, and applicable quality requirements.</div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step"><div class="industry-number">2</div><div><strong>Choose the design assumptions</strong><br>Specify the termination multiplier <em>a</em>, GE shape <em>&lambda;</em>, items per group <em>r</em>, chain parameter <em>i</em>, acceptable mean-life ratio, and the risk framework. Average and Bayesian plans also require a Beta prior.</div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step"><div class="industry-number">3</div><div><strong>Retrieve the validated sampling plan</strong><br>Use Selected Plan Explorer to obtain the selected number of groups <em>g*</em>, total sample size <em>n*=rg*</em>, test termination time <em>t<sub>0</sub>=a&mu;<sub>0</sub></em>, and the associated risk measures.</div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step"><div class="industry-number">4</div><div><strong>Draw and test the sample</strong><br>Randomly select <em>n*</em> items, arrange them into <em>g*</em> groups of <em>r</em> items, run the life test until <em>t<sub>0</sub></em>, and count the failures in the current lot.</div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step decision"><div class="industry-number">5</div><div><strong>Apply the GChSP acceptance rule</strong><br><b>Zero failures:</b> accept the lot. <b>One failure:</b> accept only when each of the preceding <em>i</em> lots had zero failures; otherwise reject. <b>More than one failure:</b> reject the lot.</div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step"><div class="industry-number">6</div><div><strong>Act and preserve the chain history</strong><br>Release an accepted lot according to the organization's procedures, or quarantine and investigate a rejected lot. Record the result because it becomes part of the preceding-lot history for future decisions.</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    "Operational use should follow the organization's approved sampling, traceability, safety, "
    "and regulatory procedures. The dashboard supports—not replaces—engineering judgement."
)

st.header("3. Three Risk Frameworks Overview")
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

st.header("4. How to Use This Dashboard")
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
