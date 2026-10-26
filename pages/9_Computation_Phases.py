"""Methodological computation flow for validated phases 3 through 9."""

from __future__ import annotations

import streamlit as st

from src.ui import render_footer, render_page_header

PHASES = (
    (
        3,
        "OC Function Formulation",
        "Define the GChSP acceptance probability from current and preceding lots.",
        "#F28C28",
    ),
    (
        4,
        "P₀ and P₁ Derivation",
        "Derive the zero- and one-failure terms and substitute them into the OC function.",
        "#7C3AED",
    ),
    (
        5,
        "Fraction Defective",
        "Map the corrected GE lifetime model and mean-life ratio to failure probability p.",
        "#D81B60",
    ),
    (6, "Input Specification", "Set classical quality points and the nine shared Beta priors.", "#D9A400"),
    (
        7,
        "Risk Computation",
        "Evaluate Classical, normalized Average, and Bayesian producer and consumer risks.",
        "#6D28D9",
    ),
    (
        8,
        "Selection of g*",
        "Choose the smallest integer g satisfying only the framework's consumer-risk restriction.",
        "#E83E8C",
    ),
    (
        9,
        "Performance Evaluation",
        "Compare sampling requirements, risks, and acceptance behavior across frameworks.",
        "#C69200",
    ),
)


def phase_card(number: int, title: str, summary: str, color: str) -> None:
    st.markdown(
        f"""
        <div class="phase-card" style="border-left-color:{color}">
          <div class="phase-number" style="background:{color}">{number}</div>
          <div>
            <div class="phase-title">PHASE {number} · {title}</div>
            <div class="phase-summary">{summary}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Computation Phases", page_icon="🧭", layout="wide")
render_page_header(
    "Phases of Results Computation",
    "A reproducible Phase 3–9 flow from the GChSP operating characteristic to framework comparison.",
)
st.markdown(
    """
    <style>
      .phase-card {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.9rem 1rem;
        margin: 0.15rem 0;
        border-left: 7px solid;
        border-radius: 0.45rem;
        background: #F7F9FC;
        box-shadow: 0 1px 2px rgba(23, 54, 93, 0.08);
      }
      .phase-number {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 2.65rem;
        height: 2.65rem;
        border-radius: 50%;
        color: white;
        font-size: 1.25rem;
        font-weight: 800;
      }
      .phase-title { color: #17365D; font-weight: 800; letter-spacing: 0.02em; }
      .phase-summary { color: #405060; margin-top: 0.2rem; }
      .phase-arrow { text-align: center; color: #8090A0; font-size: 1.35rem; line-height: 1.1; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.info(
    "The validated research specification is authoritative: this flow uses the corrected GE shape–scale model and "
    "the normalized Average-risk definitions. Producer risks and risk sums are evaluation measures only."
)
expand_all = st.toggle("Expand all mathematical details", value=False)

for position, (number, title, summary, color) in enumerate(PHASES):
    phase_card(number, title, summary, color)
    if position < len(PHASES) - 1:
        st.markdown('<div class="phase-arrow">↓</div>', unsafe_allow_html=True)

st.divider()

with st.expander("Phase 3 — OC function formulation", expanded=expand_all):
    st.markdown(
        "For a GChSP plan with number of groups $g$, items per group $r$, and chain parameter $i$, acceptance is "
        "formed from the zero-failure probability in the current lot and the one-failure probability combined with "
        "zero failures in the preceding $i$ lots."
    )
    st.latex(r"L_g(p)=P_0(p)+P_1(p)\,[P_0(p)]^i")
    st.markdown("Here $p$ is the probability that an individual item fails before the termination time.")

with st.expander("Phase 4 — Derivation of P₀, P₁, and the complete OC function", expanded=expand_all):
    st.markdown("With $n=gr$ tested items and $d$ failures, the binomial probability is")
    st.latex(r"P_d(p)=\binom{gr}{d}p^d(1-p)^{gr-d}.")
    left, right = st.columns(2)
    with left:
        st.markdown("**Zero failures**")
        st.latex(r"P_0(p)=(1-p)^{gr}")
    with right:
        st.markdown("**Exactly one failure**")
        st.latex(r"P_1(p)=gr\,p(1-p)^{gr-1}")
    st.markdown("Substitution into the chain rule gives the implemented OC function:")
    st.latex(r"\boxed{L_g(p)=(1-p)^{gr}+gr\,p(1-p)^{gr(i+1)-1}}")
    st.markdown(
        r"The implementation verifies $L_g(0)=1$, $L_g(1)=0$, $0\le L_g(p)\le1$, and monotonic decrease in $p$."
    )

with st.expander("Phase 5 — Corrected GE fraction-defective formulation", expanded=expand_all):
    st.markdown(r"The research implementation uses GE shape $\lambda>0$ and scale $\sigma>0$:")
    st.latex(r"F(t;\lambda,\sigma)=\left(1-e^{-t/\sigma}\right)^\lambda")
    st.latex(r"H_\lambda=\psi(\lambda+1)-\psi(1),\qquad \mu=\sigma H_\lambda")
    st.markdown(r"With $t_0=a\mu_0$ and mean-life ratio $\rho=\mu/\mu_0$,")
    st.latex(r"\boxed{p(\rho;a,\lambda)=\left[1-\exp\!\left(-\frac{aH_\lambda}{\rho}\right)\right]^\lambda}")
    st.latex(r"p_1=p(\rho_A;a,\lambda),\qquad p_2=p(1;a,\lambda),\qquad 0<p_1<p_2<1.")
    st.markdown(
        r"Numerical evaluation uses stable exponential functions such as `expm1`; the ordinary exponential model is not substituted when $\lambda\ne1$."
    )

with st.expander("Phase 6 — Classical quality inputs and nine Beta priors", expanded=expand_all):
    st.markdown(
        "The Classical framework uses the fixed quality-point probabilities $p_1$ and $p_2$ without a prior. "
        "Average and Bayesian calculations share one of nine fixed Beta priors in each prior–scenario unit."
    )
    st.latex(
        r"p\sim\operatorname{Beta}(\alpha_\pi,\beta_\pi),\qquad h(p)=\frac{p^{\alpha_\pi-1}(1-p)^{\beta_\pi-1}}{B(\alpha_\pi,\beta_\pi)}"
    )
    st.latex(r"\kappa=\frac{\mu_\pi(1-\mu_\pi)}{s_\pi^2}-1")
    st.latex(r"\alpha_\pi=\mu_\pi\kappa,\qquad \beta_\pi=(1-\mu_\pi)\kappa")
    st.markdown(
        r"The prior means are $\{0.032,0.063,0.094\}$ and prior standard deviations are "
        r"$\{0.047,0.054,0.062\}$, producing priors B1–B9. All resulting shape parameters must be strictly positive."
    )

with st.expander("Phase 7 — Six risks and three evaluation sums", expanded=expand_all):
    st.markdown("**Classical risks**")
    st.latex(r"PR(g)=1-L_g(p_1),\qquad CR(g)=L_g(p_2)")
    st.markdown("**Normalized Average risks**")
    st.latex(r"APR(g)=\frac{\int_0^{p_1}[1-L_g(p)]h(p)\,dp}{H(p_1)}")
    st.latex(r"ACR(g)=\frac{\int_{p_2}^{1}L_g(p)h(p)\,dp}{1-H(p_2)}")
    st.markdown("**Bayesian risks**")
    st.latex(r"BPR(g)=\frac{\int_0^{p_1}[1-L_g(p)]h(p)\,dp}{\int_0^1[1-L_g(p)]h(p)\,dp}")
    st.latex(r"BCR(g)=\frac{\int_{p_2}^{1}L_g(p)h(p)\,dp}{\int_0^1L_g(p)h(p)\,dp}")
    st.markdown("**Risk sums used only for performance evaluation**")
    st.latex(r"MSR=PR+CR,\qquad MSAR=APR+ACR,\qquad MSBR=BPR+BCR")
    st.markdown("Beta-weighted polynomial terms are evaluated through incomplete-Beta identities:")
    st.latex(
        r"\int_0^x p^u(1-p)^v h(p)\,dp="
        r"\frac{B(\alpha_\pi+u,\beta_\pi+v)}{B(\alpha_\pi,\beta_\pi)}"
        r"I_x(\alpha_\pi+u,\beta_\pi+v)."
    )
    st.markdown("Upper tails use complementary incomplete-Beta evaluation directly to avoid cancellation.")

with st.expander("Phase 8 — Consumer-risk-only selection of the smallest feasible g*", expanded=expand_all):
    st.latex(r"g_C^*=\min\{g\in\{1,\ldots,500\}:CR(g)\le\beta_0\}")
    st.latex(r"g_A^*=\min\{g\in\{1,\ldots,500\}:ACR(g)\le\beta_0\}")
    st.latex(r"g_B^*=\min\{g\in\{1,\ldots,500\}:BCR(g)\le\beta_0\}")
    st.latex(r"\beta_0=0.10\quad\text{for the primary experiment}")
    st.markdown(
        "Each framework is optimized separately. The selected integer must satisfy its own consumer-risk ceiling, "
        "and every smaller integer must fail it. No producer-risk constraint and no risk-sum objective is introduced."
    )

with st.expander("Phase 9 — Sampling, OC, sensitivity, and matched comparison outputs", expanded=expand_all):
    st.markdown("For each feasible framework-selected plan,")
    st.latex(r"n^*=r\,g^*")
    st.markdown(
        "All six risks, all three risk sums, $L(p_1)$, and $L(p_2)$ are evaluated at each framework-selected $g^*$. "
        "The same common measures are therefore available for head-to-head comparison without redefining risk."
    )
    st.latex(r"L_{g^*}\!\left(p(\rho;a,\lambda)\right),\qquad \rho\in\{2,4,6,8,10,12\}")
    st.markdown(
        r"Fixed-plan OC analysis holds $g^*$ constant while $\rho$ changes. Independently selected analysis chooses a "
        r"plan at each design ratio. Matched analysis compares Classical, Average, and Bayesian records on the same "
        r"prior–scenario key and clearly separates common-risk from own-risk summaries."
    )

render_footer()
