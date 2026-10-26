"""Runtime configuration without hard-coded machine-specific paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    project_root: Path
    results_root: Path | None
    database_url: str | None

    @property
    def backend(self) -> str:
        return "neon" if self.database_url else "local"


def discover_results_root() -> Path | None:
    configured = os.getenv("GCHSPFAM_RESULTS_DIR")
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.append(PROJECT_ROOT.parent / "gchspfam-ge-3rf-results")
    for candidate in candidates:
        marker = candidate / "outputs" / "analytics" / "selected_plans_research_ready.parquet"
        if marker.is_file():
            return candidate.resolve()
    return None


def _streamlit_database_url() -> str | None:
    try:
        import streamlit as st

        database = st.secrets.get("database", {})
        if hasattr(database, "get"):
            return database.get("url")
    except (FileNotFoundError, KeyError, RuntimeError):
        return None
    return None


def load_settings() -> Settings:
    database_url = os.getenv("NEON_READONLY_DATABASE_URL") or _streamlit_database_url()
    return Settings(
        project_root=PROJECT_ROOT,
        results_root=discover_results_root(),
        database_url=database_url,
    )
