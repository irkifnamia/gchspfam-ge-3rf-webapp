"""Shared Streamlit user-interface helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.constants import FRAMEWORKS

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
            color: #17365D;
            font-size: 1.28rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            margin: 0.15rem 0 0.55rem;
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


def sidebar_filters(options: dict[str, list[Any]], include_framework: bool = True) -> dict[str, list[Any]]:
    st.sidebar.header("Research filters")
    labels = {
        "prior_id": "Beta prior",
        "acceptable_mean_life_ratio": "Mean-life ratio ρA",
        "termination_multiplier": "Termination multiplier a",
        "ge_shape": "GE shape λ",
        "group_size_r": "Group size r",
        "chain_parameter_i": "Chain parameter i",
        "framework": "Framework",
    }
    order = [
        "prior_id",
        "acceptable_mean_life_ratio",
        "termination_multiplier",
        "ge_shape",
        "group_size_r",
        "chain_parameter_i",
    ]
    if include_framework:
        order.append("framework")
    result: dict[str, list[Any]] = {}
    for column in order:
        values = options.get(column, [])
        if column == "framework":
            values = [value for value in FRAMEWORKS if value in values]
        chosen = st.sidebar.multiselect(labels[column], values, default=values)
        if chosen and len(chosen) != len(values):
            result[column] = chosen
    return result


def dataframe_download(data: pd.DataFrame, filename: str, label: str = "Download filtered CSV") -> None:
    st.download_button(
        label,
        data=data.to_csv(index=False, float_format="%.17g").encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def render_footer() -> None:
    """Retained as a compatibility no-op; pages do not display a repeated footer."""
