"""Landing page for the GChSPFAM-GE-3RF research dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import apply_academic_layout
from src.constants import FRAMEWORK_COLORS
from src.metrics import framework_overview
from src.runtime import get_repository
from src.ui import apply_global_filters, render_data_source_badge, render_footer, render_page_header

DESIGN_PARAMETERS = pd.DataFrame(
    [
        ("g", "Number of groups", "Integer candidates 1–500; the smallest feasible value is selected"),
        ("(r, i)", "Items per group and preceding lots", "(2, 1), (3, 2), (4, 3), (5, 4)"),
        ("a", "Termination-time multiplier", "0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00"),
        ("t₀", "Test termination time", "t₀ = aμ₀"),
        ("μ₀", "Specified reference mean lifetime", "Defined by the product or testing specification"),
        ("ρ = μ/μ₀", "Mean-life ratio", "Product mean lifetime relative to μ₀"),
        ("ρA", "Acceptable mean-life ratio", "2, 4, 6, 8, 10, 12"),
        ("λ", "GE shape parameter", "1, 2, 3"),
        ("n", "Total number of tested items", "n = rg"),
        ("β₀", "Consumer-risk ceiling", "0.10 for the primary experiment"),
    ],
    columns=["Parameter", "Meaning", "Research values or definition"],
)

BETA_PRIOR_MOMENTS = (
    ("B1", 0.032, 0.047),
    ("B2", 0.032, 0.054),
    ("B3", 0.032, 0.062),
    ("B4", 0.063, 0.047),
    ("B5", 0.063, 0.054),
    ("B6", 0.063, 0.062),
    ("B7", 0.094, 0.047),
    ("B8", 0.094, 0.054),
    ("B9", 0.094, 0.062),
)


def beta_prior_table() -> pd.DataFrame:
    """Return the nine fixed Beta priors from their specified moments."""
    rows = []
    for prior_id, mean, standard_deviation in BETA_PRIOR_MOMENTS:
        concentration = mean * (1.0 - mean) / standard_deviation**2 - 1.0
        rows.append(
            {
                "Prior": prior_id,
                "Mean μπ": mean,
                "SD σπ": standard_deviation,
                "Beta απ": mean * concentration,
                "Beta βπ": (1.0 - mean) * concentration,
            }
        )
    return pd.DataFrame(rows)


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
This project develops a **Group Chain Sampling Plan (GChSP)** for truncated product-lifetime
testing under the **Generalized Exponential (GE) distribution**. The application compares three
risk frameworks while preserving one selection rule: choose the smallest number of groups that
satisfies the selected framework's consumer-risk ceiling.
"""
)

with st.expander("Research question and mathematical model", expanded=True):
    st.markdown(
        """
        - **Truncated life test:** test a sample only until the predetermined termination time
          rather than waiting for every item to fail.
        - **Current-lot evidence:** count the failures observed before termination.
        - **Chain information:** when exactly one failure occurs, also examine the outcomes of
          the preceding $i$ lots.
        - **GE conversion:** use the corrected GE model to convert the mean-life ratio into the
          item failure probability $p$.
        - **Acceptance probability:** evaluate $p$ using the complete GChSP operating-
          characteristic function $L_g(p)$.
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
        "- **Plan selection:** search integer group counts from 1 through 500 and select the first feasible count independently for each framework:"
    )
    st.latex(
        r"g_F^*=\min\left\{g\in\{1,\ldots,500\}:R_F(g)\leq0.10\right\},"
        r"\quad n_F^*=r g_F^*,\quad F\in\{C,A,B\}"
    )
    st.markdown(
        r"- **Framework restriction:** $R_C=CR$, $R_A=ACR$, and $R_B=BCR$."
        "\n- **Evaluation only:** producer risks and risk sums are calculated only after "
        r"$g_F^*$ is selected."
    )

with st.expander("Design Parameters & Scenario ID", expanded=False):
    st.markdown(
        r"""
        - A **Scenario ID** is the deterministic label for one specific combination of
          $(\rho_A,a,\lambda,r,i)$.
        - The design contains **576 Scenario IDs**: 6 acceptable mean-life ratios × 8
          termination multipliers × 3 GE shapes × 4 paired $(r,i)$ settings.
        - A Scenario ID does **not** include the Beta prior or risk framework. Each scenario is
          crossed with B1–B9 to form 5,184 prior–scenario units, and each unit has separate
          Classical, Average, and Bayesian selected-plan records.
        - Consequently, `S001 / B1 / Bayesian` identifies a framework result, while `S001`
          alone identifies only its underlying design-parameter combination.
        """
    )
    st.dataframe(DESIGN_PARAMETERS, width="stretch", hide_index=True)
    st.caption(
        "The four (r, i) combinations are paired design settings; r and i are not crossed "
        "independently in this experiment."
    )

with st.expander("Nine fixed Beta prior combinations", expanded=False):
    st.markdown(
        r"""
        - $p$ is the uncertain lot failure probability before observing the current lot.
        - The subscript $\pi$ means **prior distribution**; it is not the mathematical constant
          $\pi=3.14159\ldots$.
        - $\mu_\pi$ is the specified prior mean of $p$.
        - $\sigma_\pi$ is the specified prior standard deviation of $p$.
        - $\kappa$ (kappa) is the implied concentration calculated from those two moments.
        - $\alpha_\pi$ and $\beta_\pi$ are the positive Beta shape parameters obtained from
          $\mu_\pi$, $\sigma_\pi$, and $\kappa$.
        """
    )
    st.latex(r"p\sim\operatorname{Beta}(\alpha_\pi,\beta_\pi)")
    st.latex(
        r"\kappa=\frac{\mu_\pi(1-\mu_\pi)}{\sigma_\pi^2}-1,\qquad"
        r"\alpha_\pi=\mu_\pi\kappa,\qquad\beta_\pi=(1-\mu_\pi)\kappa"
    )
    st.dataframe(
        beta_prior_table(),
        column_config={
            "Mean μπ": st.column_config.NumberColumn(format="%.3f"),
            "SD σπ": st.column_config.NumberColumn(format="%.3f"),
            "Beta απ": st.column_config.NumberColumn(format="%.8f"),
            "Beta βπ": st.column_config.NumberColumn(format="%.8f"),
        },
        width="stretch",
        hide_index=True,
    )
    st.caption("The same selected prior is used for Average and Bayesian calculations; Classical risks ignore it.")

metric_columns = st.columns(5)
metric_columns[0].metric("Candidate records", f"{candidate_records:,}")
metric_columns[1].metric("Selected plans", f"{len(selected):,}")
metric_columns[2].metric("Matched units", f"{len(matched_units):,}")
metric_columns[3].metric("Frameworks", "3")
metric_columns[4].metric("Consumer-risk ceiling", "0.10")

st.info(
    "All plans use consumer-risk-only optimization. Producer risks and risk sums are evaluated "
    "after selection; they are never used to choose g⁎."
)

st.header("2. Industry Application")
st.markdown(
    """
The following simulated workflow shows how a quality or reliability team can move from receiving
a production lot to making and documenting a GChSP decision. The displayed example is drawn from
the **currently filtered validated results**, so its selected plan and risks are computed values.
"""
)

example_pool = selected[selected["framework"] == "Bayesian"]
example = example_pool.sort_values(["scenario_id", "prior_id"]).iloc[0]
example_scenario = str(example["scenario_id"])
example_prior = str(example["prior_id"])
example_ratio = float(example["acceptable_mean_life_ratio"])
example_termination = float(example["termination_multiplier"])
example_shape = int(example["ge_shape"])
example_r = int(example["group_size_r"])
example_i = int(example["chain_parameter_i"])
example_g = int(example["selected_g"])
example_n = int(example["selected_n"])
example_consumer_risk = float(example["framework_consumer_risk"])

st.info(
    f"Worked example: {example_scenario} / {example_prior}, Bayesian framework — "
    f"ρA={example_ratio:g}, a={example_termination:g}, λ={example_shape}, "
    f"(r, i)=({example_r}, {example_i}), selected g⁎={example_g}, n⁎={example_n}, "
    f"BCR={example_consumer_risk:.6f}."
)
st.markdown(
    """
    <style>
      .industry-flow {
        display: flex;
        flex-direction: column;
        gap: 0.38rem;
        margin: 0.8rem 0 1.2rem;
      }
      .industry-step {
        align-items: flex-start;
        background: #F3F7FC;
        border: 1px solid #C8D7E8;
        border-left: 6px solid #17365D;
        border-radius: 0.55rem;
        display: grid;
        gap: 0.75rem;
        grid-template-columns: 2.4rem 1fr;
        padding: 0.85rem 1rem;
      }
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
      .industry-step strong { color: #17365D; font-size: 1.02rem; }
      .industry-step ul { margin: 0.42rem 0 0; padding-left: 1.15rem; }
      .industry-step li { margin: 0.18rem 0; }
      .industry-arrow { color: #4C78A8; font-size: 1.3rem; line-height: 1; text-align: center; }
    </style>
    <div class="industry-flow">
      <div class="industry-step"><div class="industry-number">1</div><div><strong>Receive and register the production lot</strong><ul><li>Assign a traceable lot identifier and record the supplier, product, quantity, and receipt date.</li><li>Confirm that the product belongs to the population for which the sampling plan was designed.</li><li>Identify the specified reference mean lifetime &mu;<sub>0</sub> and applicable quality requirements.</li></ul></div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step"><div class="industry-number">2</div><div><strong>Confirm the statistical design</strong><ul><li>Use the mean-life ratio, termination multiplier, GE shape, group size, and chain parameter displayed in the worked example above.</li><li>Use the Bayesian framework and displayed Beta prior; another framework must use its own selected plan.</li><li>Verify that the GE lifetime assumption and parameter choices remain defensible for the product.</li></ul></div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step"><div class="industry-number">3</div><div><strong>Retrieve and review the selected plan</strong><ul><li>Open Selected Plan Explorer and locate the worked-example scenario and prior.</li><li>Record the computed <em>g</em><sup>*</sup>, <em>n</em><sup>*</sup>=<em>r</em><em>g</em><sup>*</sup>, acceptance probabilities, and all six risk values.</li><li>Confirm that the plan's own consumer risk satisfies the 0.10 ceiling before testing.</li></ul></div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step"><div class="industry-number">4</div><div><strong>Prepare the sample and test</strong><ul><li>Randomly select the required <em>n</em><sup>*</sup> representative items from the received lot.</li><li>Arrange the items into <em>g</em><sup>*</sup> groups of <em>r</em> items using a documented procedure.</li><li>Set <em>t<sub>0</sub>=a&mu;<sub>0</sub></em>; confirm equipment calibration, operating conditions, and the failure definition.</li></ul></div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step"><div class="industry-number">5</div><div><strong>Run the truncated life test</strong><ul><li>Test all sampled items under the specified conditions until <em>t<sub>0</sub></em>.</li><li>Record every failure time and count the current lot's total failures <em>d</em>.</li><li>Do not change the termination time, sample size, or failure definition after observing results.</li></ul></div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step"><div class="industry-number">6</div><div><strong>Apply the GChSP decision rule</strong><ul><li><b>If d=0:</b> accept the current lot.</li><li><b>If d=1:</b> inspect the preceding <em>i</em> lot records; accept only if all had zero failures, otherwise reject.</li><li><b>If d&gt;1:</b> reject the current lot.</li></ul></div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step"><div class="industry-number">7</div><div><strong>Control lot disposition</strong><ul><li>For an accepted lot, complete the organization's authorization and release procedure.</li><li>For a rejected lot, quarantine it and initiate the approved investigation, supplier, rework, or retest process.</li><li>Do not interpret acceptance as proof that every item is failure-free.</li></ul></div></div>
      <div class="industry-arrow">&#8595;</div>
      <div class="industry-step"><div class="industry-number">8</div><div><strong>Record, update, and review</strong><ul><li>Store the inputs, sampled-item IDs, failure data, decision, and responsible personnel.</li><li>Update the chain history because this result affects future lots when <em>d=1</em>.</li><li>Periodically review whether the GE model, prior information, and process conditions remain valid before reusing the plan.</li></ul></div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    "This is a simulated implementation guide. Operational use must follow the organization's "
    "approved sampling, traceability, safety, and regulatory procedures."
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
4. Use **L(p) Explorer** and **Sensitivity Explorer** to study acceptance behavior across
   mean-life ratios and the effects of the design parameters.
5. Use **General Comparison** and **Head-to-Head Comparison** for framework-level comparisons,
   then consult **Chart Gallery** for publication-quality figures.
6. Visit **Phases** for the complete computational explanation and **Downloads** to export
   filtered research-ready data for independent analysis.
"""
)

render_footer()
