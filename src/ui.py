"""Shared Streamlit user-interface helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
UUM_LOGO = ROOT / "assets" / "branding" / "uum.png"
NAVIGATION_LINKS = (
    ("pages/9_Computation_Phases.py", "PHASES"),
    ("app.py", "OVERVIEW"),
    ("pages/5_Candidate_Explorer.py", "ALL CANDIDATE EXPLORER"),
    ("pages/1_Selected_Plan_Explorer.py", "SELECTED PLAN EXPLORER"),
    ("pages/6_Selected_G_Explorer.py", "SELECTED G EXPLORER"),
    ("pages/3_OC_Explorer.py", "OC EXPLORER"),
    ("pages/4_Sensitivity_Explorer.py", "SENSITIVITY EXPLORER"),
    ("pages/2_Framework_Comparison.py", "GENERAL COMPARISON"),
    ("pages/8_Head_to_Head_Comparison.py", "HEAD-TO-HEAD COMPARISON"),
    ("pages/6_Chart_Gallery.py", "CHART GALLERY"),
    ("pages/7_Validation_and_Downloads.py", "DOWNLOADS"),
)
GLOBAL_FILTER_OPTIONS = {
    "prior_id": [f"B{index}" for index in range(1, 10)],
    "acceptable_mean_life_ratio": [2, 4, 6, 8, 10, 12],
    "termination_multiplier": [0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00],
    "ge_shape": [1, 2, 3],
    "group_size_r": [2, 3, 4, 5],
    "chain_parameter_i": [1, 2, 3, 4],
}
GLOBAL_FILTER_LABELS = {
    "prior_id": "Beta prior",
    "acceptable_mean_life_ratio": "Mean-life ratio ρ / ρA",
    "termination_multiplier": "Termination multiplier a",
    "ge_shape": "GE shape λ",
    "group_size_r": "Group size r",
    "chain_parameter_i": "Chain parameter i",
}


def _global_filter_key(column: str) -> str:
    return f"global_filter_{column}"


def _clear_global_filters() -> None:
    for column in GLOBAL_FILTER_OPTIONS:
        st.session_state[_global_filter_key(column)] = []


def active_global_filters() -> dict[str, list[Any]]:
    """Return nonempty global sidebar selections from session state."""
    return {
        column: list(st.session_state.get(_global_filter_key(column), []))
        for column in GLOBAL_FILTER_OPTIONS
        if st.session_state.get(_global_filter_key(column), [])
    }


def apply_global_filters(
    frame: pd.DataFrame,
    *,
    mean_ratio_column: str | None = None,
) -> pd.DataFrame:
    """Apply the shared sidebar filters to any compatible research table."""
    result = frame
    for column, values in active_global_filters().items():
        target = mean_ratio_column if column == "acceptable_mean_life_ratio" and mean_ratio_column else column
        if target in result.columns:
            result = result[result[target].isin(values)]
    return result.copy()


def render_global_filters() -> None:
    """Render persistent design filters shared by every application page."""
    with st.sidebar.expander("GLOBAL FILTERS", expanded=False):
        st.caption("Leave a field empty to include all values.")
        for column, options in GLOBAL_FILTER_OPTIONS.items():
            st.multiselect(
                GLOBAL_FILTER_LABELS[column],
                options,
                key=_global_filter_key(column),
                placeholder="All",
            )
        st.button("Clear global filters", on_click=_clear_global_filters, use_container_width=True)


def render_application_sidebar() -> None:
    """Render branded navigation and research attribution on every page."""
    st.sidebar.markdown(
        """
        <style>
          [data-testid="stSidebar"] [data-testid="stPageLink"] p {
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.01em;
          }
          .gchsp-sidebar-title {
            background: linear-gradient(135deg, #0B2D5B 0%, #17365D 72%, #244C7A 100%);
            border: 2px solid #C9A227;
            border-radius: 0.45rem;
            box-shadow: 0 2px 6px rgba(23, 54, 93, 0.2);
            color: #F4CF57;
            font-size: 1.28rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            margin: 0.25rem 0 0.65rem;
            padding: 0.48rem 0.4rem;
            text-align: center;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.image(str(UUM_LOGO), width="stretch")
    st.sidebar.markdown('<div class="gchsp-sidebar-title">GChSP-GE-3RF</div>', unsafe_allow_html=True)
    for path, label in NAVIGATION_LINKS:
        try:
            st.sidebar.page_link(path, label=label)
        except KeyError:
            # Direct AppTest execution has no multipage registry. Production
            # Streamlit runs always use the page links above.
            st.sidebar.markdown(f"**{label}**")
    st.sidebar.divider()
    render_global_filters()
    st.sidebar.divider()
    st.sidebar.markdown(
        """
        **Researcher**

        Aiman Fikri Jamaludin

        **Supervisors**

        - Dr Mohd Azri Pawan Teh
        - Dr Nazrina Aziz

        **Institution**

        Universiti Utara Malaysia (UUM)
        """
    )
    st.sidebar.divider()


def render_page_header(title: str, subtitle: str) -> None:
    render_application_sidebar()
    st.markdown(
        f"""
        <div style="padding:1.1rem 1.25rem;border-left:6px solid #C9A227;background:#F3F6F9;margin-bottom:1rem">
          <h1 style="margin:0;color:#17365D">{title}</h1>
          <p style="margin:.45rem 0 0;color:#405060">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_data_source_badge(_repository: Any) -> None:
    """Retained as a compatibility no-op; page-level source badges are hidden."""


def dataframe_download(data: pd.DataFrame, filename: str, label: str = "Download filtered CSV") -> None:
    st.download_button(
        label,
        data=data.to_csv(index=False, float_format="%.17g").encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def render_footer() -> None:
    """Retained as a compatibility no-op; pages do not display a repeated footer."""
