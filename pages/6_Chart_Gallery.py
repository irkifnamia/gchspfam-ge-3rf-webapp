"""Complete gallery of validated Stage 9 figures."""

from __future__ import annotations

import streamlit as st

from src.runtime import get_repository
from src.ui import render_data_source_badge, render_footer, render_page_header

st.set_page_config(page_title="Chart Gallery", page_icon="🖼️", layout="wide")
render_page_header(
    "Chart Gallery",
    "Browse all 39 validated Stage 9 figures alongside the interactive analyses.",
)
repository = get_repository()
render_data_source_badge(repository)
paths = repository.chart_paths()

groups = {
    "A — Sampling and acceptance": "A",
    "B — Risk performance": "B",
    "C — Sensitivity": "C",
    "D — Discrimination": "D",
    "E — Pairwise comparisons": "E",
}
label = st.selectbox("Figure group", list(groups))
prefix = groups[label]
chosen = [path for path in paths if path.name.startswith(prefix)]

if not chosen:
    st.warning("No packaged chart files were found. Run `scripts/sync_validated_assets.py` before deployment.")
    st.stop()

for start in range(0, len(chosen), 2):
    columns = st.columns(2)
    for column, path in zip(columns, chosen[start : start + 2], strict=False):
        with column:
            st.image(str(path), width="stretch")
            st.caption(path.stem.replace("_", " "))

st.caption(
    f"Showing {len(chosen)} of {len(paths)} validated figures. Static images are preserved at their original resolution."
)
render_footer()
