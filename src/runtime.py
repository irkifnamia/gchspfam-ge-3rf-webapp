"""Construct and cache the configured read-only repository."""

from __future__ import annotations

import streamlit as st

from src.config import load_settings
from src.repository import LocalResultsRepository, NeonResultsRepository, ResearchRepository


@st.cache_resource(show_spinner="Connecting to the validated research data…")
def get_repository() -> ResearchRepository:
    settings = load_settings()
    if settings.database_url:
        return NeonResultsRepository(settings.database_url, settings.project_root)
    if settings.results_root is None:
        raise RuntimeError(
            "No Neon read-only URL is configured and the sibling gchspfam-ge-3rf-results project was not found. "
            "Set GCHSPFAM_RESULTS_DIR or configure .streamlit/secrets.toml."
        )
    return LocalResultsRepository(settings.results_root, settings.project_root)
