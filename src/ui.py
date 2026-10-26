"""Shared Streamlit user-interface helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.constants import FRAMEWORKS


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div style="padding:1.1rem 1.25rem;border-left:6px solid #C9A227;background:#F3F6F9;margin-bottom:1rem">
          <h1 style="margin:0;color:#17365D">{title}</h1>
          <p style="margin:.45rem 0 0;color:#405060">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_data_source_badge(repository: Any) -> None:
    if repository.backend_name == "neon":
        st.caption("Data source: Neon PostgreSQL · read-only production connection")
    else:
        st.caption("Data source: validated local Stage 7–10 outputs · read-only mode")


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
    st.divider()
    st.caption(
        "GChSPFAM-GE-3RF Research Analytics · Consumer-risk-only optimization · "
        "Producer risks and risk sums are evaluation measures, not selection criteria."
    )
