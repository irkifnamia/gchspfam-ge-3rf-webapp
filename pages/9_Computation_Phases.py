"""Methodological computation flow for validated phases 3 through 9."""

from __future__ import annotations

import streamlit as st

from src.ui import render_footer, render_page_header

st.set_page_config(page_title="Phases", page_icon="🧭", layout="wide")
render_page_header(
    "Phases",
    "A reproducible Phase 3–9 flow from the GChSP operating characteristic to framework comparison.",
)
expand_all = st.toggle("Expand all mathematical details", value=False)
st.subheader("How the result datasets were computed")
st.markdown(
    r"""
| Phase | Input used by the computation | Calculation performed | Result passed forward |
|---|---|---|---|
| **3 — OC formulation** | Candidate plan parameters $(g,r,i)$ and failure probability $p$ | Define the probability that the current lot is accepted under the group-chain rule | One OC expression used by every risk framework |
| **4 — $P_0$ and $P_1$** | Binomial failure counts for $n=gr$ items | Derive the zero-failure and one-failure contributions and evaluate them for $g=1,\ldots,500$ | Candidate-level $L_g(p)$ values |
| **5 — Fraction defective** | GE shape $\lambda$, termination multiplier $a$, and mean-life ratio $\rho$ | Convert lifetime assumptions into $p_1$ and $p_2$ using the corrected GE mean–scale relationship | Quality-point failure probabilities for 576 design scenarios |
| **6 — Inputs and priors** | Nine prior mean/SD pairs and 576 scenarios | Convert prior moments to Beta shapes and pair each prior with every scenario | 5,184 prior–scenario analysis units |
| **7 — Risk computation** | $L_g(p)$, $p_1$, $p_2$, and the Beta prior | Compute PR, CR, APR, ACR, BPR, BCR and the three descriptive sums for every candidate $g$ | 2,592,000 complete candidate records |
| **8 — Selection of $g^*$** | Framework-specific consumer risk for $g=1,\ldots,500$ | Select the first integer satisfying the 0.10 consumer-risk ceiling separately for each framework | 15,552 selected-plan records |
| **9 — Evaluation and comparison** | The selected plans and their common risk measures | Build matched results, fixed-plan OC evaluations, sensitivity summaries, and comparisons | Research-ready datasets, tables, and figures |
"""
)
st.caption("Open each phase below for the formula, computational action, and resulting data product.")

with st.expander("Phase 3 — OC function formulation", expanded=expand_all):
    st.markdown(
        "For a GChSP plan with number of groups $g$, items per group $r$, and chain parameter $i$, acceptance is "
        "formed from the zero-failure probability in the current lot and the one-failure probability combined with "
        "zero failures in the preceding $i$ lots."
    )
    st.latex(r"L_g(p)=P_0(p)+P_1(p)\,[P_0(p)]^i")
    st.markdown("Here $p$ is the probability that an individual item fails before the termination time.")
    st.markdown("**How this generated the results**")
    st.markdown(
        "The experiment created candidate plans for every integer $g$ from 1 to 500 and each configured $(r,i)$ "
        "pair. This same acceptance mechanism was used for Classical, Average, and Bayesian calculations; the "
        "frameworks differ in how they evaluate risk, not in the sampling rule or OC function."
    )
    st.markdown("**Output of this phase:** a common mathematical template for calculating acceptance probability.")

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
    st.markdown("**How this generated the results**")
    st.markdown(
        r"For each prior–scenario unit, the program formed arrays containing $g=1,\ldots,500$, calculated "
        r"$n=gr$, and evaluated both OC terms with vectorized NumPy power operations. The resulting $L_g(p_1)$ "
        r"and $L_g(p_2)$ values became the Classical acceptance probabilities and the building blocks for the "
        r"Beta-weighted integrals."
    )
    st.markdown("**Output of this phase:** candidate $g$, candidate $n$, $L(p_1)$, and $L(p_2)$ values.")

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
    st.markdown("**How this generated the results**")
    st.markdown(
        r"The program calculated $H_\lambda$ from the digamma function for each GE shape. It then evaluated "
        r"$p_1$ at the acceptable design ratio $\rho_A$ and $p_2$ at $\rho=1$ for every combination of "
        r"$\rho_A$, $a$, $\lambda$, $r$, and $i$. Every scenario was checked to satisfy $0<p_1<p_2<1$. "
        r"Because $p_2$ does not contain $\rho_A$, consumer-risk-selected $g^*$ is theoretically invariant to "
        r"the acceptable design ratio when the other parameters are fixed."
    )
    st.markdown("**Output of this phase:** one corrected $(p_1,p_2)$ pair for each of the 576 design scenarios.")

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
    st.markdown("**How this generated the results**")
    st.markdown(
        r"Each of the nine mean/SD pairs was converted once to $(\alpha_\pi,\beta_\pi)$ and its moments were "
        r"checked numerically. The nine fixed priors were crossed with the 576 design scenarios, producing "
        r"$576\times9=5{,}184$ prior–scenario units. Within a unit, the same prior was used for Average and "
        r"Bayesian risks. Classical risks were repeated for reporting but were verified to be prior-independent."
    )
    st.markdown(
        "**Output of this phase:** Beta parameters, prior good-region probability, and prior bad-region probability for each analysis unit."
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
    st.markdown("**How this generated the results**")
    st.markdown(
        "For every analysis unit and all 500 candidate values of $g$, the program first calculated PR and CR "
        "directly from $L_g(p_1)$ and $L_g(p_2)$. It evaluated the Average and Bayesian numerators and "
        "denominators through log-Beta and regularized incomplete-Beta identities, using complementary upper-tail "
        "functions where subtraction from one would lose precision. APR and ACR were normalized by prior-region "
        "probabilities; BPR and BCR were normalized by the total rejection or acceptance probability."
    )
    st.markdown(
        r"The three sums were then formed row by row: $MSR=PR+CR$, $MSAR=APR+ACR$, and $MSBR=BPR+BCR$. "
        r"This calculation produced $5{,}184\times500=2{,}592{,}000$ candidate records containing all six risks."
    )
    st.markdown("**Output of this phase:** the complete candidate-level research dataset.")

with st.expander("Phase 8 — Consumer-risk-only selection of the smallest feasible g⁎", expanded=expand_all):
    st.latex(r"g_C^*=\min\{g\in\{1,\ldots,500\}:CR(g)\le\beta_0\}")
    st.latex(r"g_A^*=\min\{g\in\{1,\ldots,500\}:ACR(g)\le\beta_0\}")
    st.latex(r"g_B^*=\min\{g\in\{1,\ldots,500\}:BCR(g)\le\beta_0\}")
    st.latex(r"\beta_0=0.10\quad\text{for the primary experiment}")
    st.markdown(
        "Each framework is optimized separately. The selected integer must satisfy its own consumer-risk ceiling, "
        "and every smaller integer must fail it. No producer-risk constraint and no risk-sum objective is introduced."
    )
    st.markdown("**How this generated the results**")
    st.markdown(
        "Within each prior–scenario unit, the candidate rows were kept in ascending integer order. Three Boolean "
        "feasibility columns recorded whether CR, ACR, or BCR was at most 0.10. The first `True` row in each "
        "column supplied the framework's $g^*$; $n^*=rg^*$ was then calculated. The selected row and the preceding "
        "row were checked to confirm feasibility and integer minimality. Infeasible units would have been retained "
        "with missing selected-plan values rather than being assigned $g=500$."
    )
    st.markdown(
        "**Output of this phase:** three framework-selected plans for every analysis unit, giving "
        r"$5{,}184\times3=15{,}552$ selected-plan records."
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
    st.markdown("**How this generated the results**")
    st.markdown(
        r"Every framework-selected $g^*$ was joined back to the common candidate measures so that PR, APR, BPR, "
        r"CR, ACR, BCR, MSR, MSAR, and MSBR were all evaluated at the same selected plan. The three framework "
        r"records were pivoted into 5,184 matched prior–scenario rows. After confirming design-ratio invariance, "
        r"the selected records were reduced to 2,592 unique fixed plans. Each plan was held constant while the "
        r"corrected GE mapping was reevaluated at $\rho\in\{2,4,6,8,10,12\}$, producing "
        r"$2{,}592\times6=15{,}552$ OC evaluation rows. These outputs then supplied feasibility summaries, sensitivity tables, "
        r"head-to-head comparisons, downloadable datasets, and the academic figures shown in the application."
    )
    st.markdown("**Output of this phase:** the research-ready analytical tables and visual reporting products.")

render_footer()
