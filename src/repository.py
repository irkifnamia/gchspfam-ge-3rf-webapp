"""Read-only data access for local validated outputs and Neon PostgreSQL."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Iterable
from functools import cached_property
from pathlib import Path
from threading import RLock
from typing import Any

import pandas as pd
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from sqlalchemy import Engine, create_engine, text

from src.constants import EXPECTED_COUNTS, FILTER_COLUMNS


def _filtered_frame(frame: pd.DataFrame, filters: dict[str, Iterable[Any]] | None) -> pd.DataFrame:
    result = frame
    for column, values in (filters or {}).items():
        chosen = list(values)
        if chosen:
            result = result[result[column].isin(chosen)]
    return result.copy()


def _normalise_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    return url


class ResearchRepository(ABC):
    backend_name: str

    @abstractmethod
    def selected_plans(self, filters: dict[str, Iterable[Any]] | None = None) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def matched_results(self, filters: dict[str, Iterable[Any]] | None = None) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def fixed_plan_oc(self, filters: dict[str, Iterable[Any]] | None = None) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def candidate_trace(self, scenario_id: str, prior_id: str) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def dataset_counts(self) -> dict[str, int]:
        raise NotImplementedError

    def filter_options(self) -> dict[str, list[Any]]:
        selected = self.selected_plans()
        return {
            column: sorted(selected[column].dropna().unique().tolist())
            for column in FILTER_COLUMNS
            if column in selected.columns
        }

    def scenario_prior_index(self) -> pd.DataFrame:
        columns = [
            "scenario_id",
            "prior_id",
            "acceptable_mean_life_ratio",
            "termination_multiplier",
            "ge_shape",
            "group_size_r",
            "chain_parameter_i",
        ]
        return self.selected_plans()[columns].drop_duplicates().sort_values(["scenario_id", "prior_id"])

    def validation_summary(self) -> dict[str, Any]:
        return {}

    def chart_paths(self) -> list[Path]:
        return []


class LocalResultsRepository(ResearchRepository):
    backend_name = "local"

    def __init__(self, results_root: Path, project_root: Path) -> None:
        self.results_root = results_root
        self.project_root = project_root
        self.analytics_root = results_root / "outputs" / "analytics"
        self.candidate_root = results_root / "outputs" / "candidates" / "stage6_parquet"

    @cached_property
    def _selected(self) -> pd.DataFrame:
        return pd.read_parquet(self.analytics_root / "selected_plans_research_ready.parquet")

    @cached_property
    def _matched(self) -> pd.DataFrame:
        return pd.read_parquet(self.analytics_root / "matched_framework_results.parquet")

    @cached_property
    def _fixed_oc(self) -> pd.DataFrame:
        return pd.read_csv(
            self.results_root / "outputs" / "stage9" / "data" / "fixed_plan_oc_evaluations.csv",
            float_precision="round_trip",
        )

    def selected_plans(self, filters: dict[str, Iterable[Any]] | None = None) -> pd.DataFrame:
        return _filtered_frame(self._selected, filters)

    def matched_results(self, filters: dict[str, Iterable[Any]] | None = None) -> pd.DataFrame:
        return _filtered_frame(self._matched, filters)

    def fixed_plan_oc(self, filters: dict[str, Iterable[Any]] | None = None) -> pd.DataFrame:
        return _filtered_frame(self._fixed_oc, filters)

    def candidate_trace(self, scenario_id: str, prior_id: str) -> pd.DataFrame:
        dataset = ds.dataset(self.candidate_root, format="parquet")
        predicate = (ds.field("scenario_id") == scenario_id) & (ds.field("prior_id") == prior_id)
        frame = dataset.to_table(filter=predicate).to_pandas()
        return frame.sort_values("candidate_g", kind="stable").reset_index(drop=True)

    def dataset_counts(self) -> dict[str, int]:
        parts = sorted(self.candidate_root.glob("*.parquet"))
        return {
            "candidate_records": sum(pq.ParquetFile(path).metadata.num_rows for path in parts),
            "selected_records": len(self._selected),
            "matched_records": len(self._matched),
            "candidate_partitions": len(parts),
            "charts": len(self.chart_paths()),
        }

    def validation_summary(self) -> dict[str, Any]:
        path = self.results_root / "outputs" / "stage10" / "verification" / "final_validation_summary.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

    def chart_paths(self) -> list[Path]:
        packaged = sorted((self.project_root / "assets" / "charts").glob("*.png"))
        if packaged:
            return packaged
        return sorted((self.results_root / "outputs" / "stage9" / "charts").glob("*.png"))

    def stage8_table(self, filename: str) -> pd.DataFrame:
        allowed = {
            "acceptance_probability_pairwise.csv",
            "beta_prior_sensitivity.csv",
            "common_risk_comparisons.csv",
            "discrimination_performance.csv",
            "feasibility_and_ordering_checks.csv",
            "framework_descriptive_summary.csv",
            "gchsp_parameter_sensitivity.csv",
            "ge_shape_sensitivity.csv",
            "mean_ratio_sensitivity.csv",
            "own_risk_comparisons.csv",
            "sampling_requirements_pairwise.csv",
            "termination_sensitivity.csv",
        }
        if filename not in allowed:
            raise ValueError(f"Unsupported Stage 8 table: {filename}")
        return pd.read_csv(self.analytics_root / "stage8" / filename, float_precision="round_trip")


class NeonResultsRepository(ResearchRepository):
    backend_name = "neon"

    def __init__(self, database_url: str, project_root: Path) -> None:
        self.project_root = project_root
        self.engine: Engine = create_engine(
            _normalise_database_url(database_url),
            pool_pre_ping=True,
            pool_recycle=240,
            connect_args={"connect_timeout": 15},
        )
        self._candidate_cache: OrderedDict[tuple[str, str], pd.DataFrame] = OrderedDict()
        self._candidate_cache_lock = RLock()

    @staticmethod
    def _where(filters: dict[str, Iterable[Any]] | None, allowed: set[str]) -> tuple[str, dict[str, Any]]:
        clauses: list[str] = []
        parameters: dict[str, Any] = {}
        for column, values in (filters or {}).items():
            if column not in allowed:
                raise ValueError(f"Unsupported filter column: {column}")
            chosen = list(values)
            if not chosen:
                continue
            names = []
            for position, value in enumerate(chosen):
                name = f"{column}_{position}"
                names.append(f":{name}")
                parameters[name] = value
            clauses.append(f"{column} IN ({', '.join(names)})")
        return (" WHERE " + " AND ".join(clauses) if clauses else ""), parameters

    def _query(self, sql: str, parameters: dict[str, Any] | None = None) -> pd.DataFrame:
        with self.engine.connect() as connection:
            return pd.read_sql_query(text(sql), connection, params=parameters or {})

    def _snapshot_path(self, filename: str) -> Path:
        return self.project_root / "data" / "analytics" / filename

    @property
    def uses_packaged_analytics(self) -> bool:
        filenames = (
            "selected_plans_research_ready.parquet",
            "matched_framework_results.parquet",
            "fixed_plan_oc_evaluations.parquet",
        )
        return all(self._snapshot_path(filename).is_file() for filename in filenames)

    @cached_property
    def _selected(self) -> pd.DataFrame:
        snapshot = self._snapshot_path("selected_plans_research_ready.parquet")
        if snapshot.is_file():
            return pd.read_parquet(snapshot)
        return self._query("SELECT * FROM research.selected_plans ORDER BY scenario_id, prior_id, framework")

    @cached_property
    def _matched(self) -> pd.DataFrame:
        snapshot = self._snapshot_path("matched_framework_results.parquet")
        if snapshot.is_file():
            return pd.read_parquet(snapshot)
        return self._query("SELECT * FROM research.matched_framework_results ORDER BY scenario_id, prior_id")

    @cached_property
    def _fixed_oc(self) -> pd.DataFrame:
        snapshot = self._snapshot_path("fixed_plan_oc_evaluations.parquet")
        if snapshot.is_file():
            return pd.read_parquet(snapshot)
        return self._query("SELECT * FROM research.fixed_plan_oc ORDER BY fixed_plan_id, evaluation_mean_life_ratio")

    def selected_plans(self, filters: dict[str, Iterable[Any]] | None = None) -> pd.DataFrame:
        self._where(filters, set(FILTER_COLUMNS))
        return _filtered_frame(self._selected, filters)

    def matched_results(self, filters: dict[str, Iterable[Any]] | None = None) -> pd.DataFrame:
        allowed = set(FILTER_COLUMNS) - {"framework"}
        self._where(filters, allowed)
        return _filtered_frame(self._matched, filters)

    def fixed_plan_oc(self, filters: dict[str, Iterable[Any]] | None = None) -> pd.DataFrame:
        allowed = set(FILTER_COLUMNS) - {"acceptable_mean_life_ratio"}
        self._where(filters, allowed)
        return _filtered_frame(self._fixed_oc, filters)

    def _candidate_trace_cached(self, scenario_id: str, prior_id: str) -> pd.DataFrame:
        key = (scenario_id, prior_id)
        with self._candidate_cache_lock:
            cached = self._candidate_cache.get(key)
            if cached is not None:
                self._candidate_cache.move_to_end(key)
                return cached

        frame = self._query(
            "SELECT * FROM research.candidate_results "
            "WHERE scenario_id=:scenario_id AND prior_id=:prior_id ORDER BY candidate_g",
            {"scenario_id": scenario_id, "prior_id": prior_id},
        )
        with self._candidate_cache_lock:
            self._candidate_cache[key] = frame
            self._candidate_cache.move_to_end(key)
            while len(self._candidate_cache) > 32:
                self._candidate_cache.popitem(last=False)
        return frame

    def candidate_trace(self, scenario_id: str, prior_id: str) -> pd.DataFrame:
        return self._candidate_trace_cached(scenario_id, prior_id).copy()

    @cached_property
    def _dataset_counts(self) -> dict[str, int]:
        validation_path = self.project_root / "data" / "neon_deployment_validation.json"
        if validation_path.is_file():
            payload = json.loads(validation_path.read_text(encoding="utf-8"))
            database = payload.get("database", {})
            required = {
                "candidate_records",
                "selected_records",
                "matched_records",
                "candidate_partitions",
            }
            if required.issubset(database):
                return {
                    name: int(database[name])
                    for name in (
                        "candidate_records",
                        "selected_records",
                        "matched_records",
                        "candidate_partitions",
                    )
                }

        row = self._query(
            "SELECT "
            "(SELECT count(*) FROM research.candidate_results) AS candidate_records, "
            "(SELECT count(*) FROM research.selected_plans) AS selected_records, "
            "(SELECT count(*) FROM research.matched_framework_results) AS matched_records, "
            "(SELECT count(*) FROM research.import_manifest WHERE dataset='candidates' AND status='complete') "
            "AS candidate_partitions"
        ).iloc[0]
        return {
            "candidate_records": int(row.candidate_records),
            "selected_records": int(row.selected_records),
            "matched_records": int(row.matched_records),
            "candidate_partitions": int(row.candidate_partitions),
        }

    def dataset_counts(self) -> dict[str, int]:
        return {**self._dataset_counts, "charts": len(self.chart_paths())}

    @cached_property
    def _validation_summary(self) -> dict[str, Any]:
        frame = self._query("SELECT payload FROM research.validation_summary WHERE name='stage10_final'")
        if frame.empty:
            return {}
        payload = frame.iloc[0, 0]
        return payload if isinstance(payload, dict) else json.loads(payload)

    def validation_summary(self) -> dict[str, Any]:
        return dict(self._validation_summary)

    def chart_paths(self) -> list[Path]:
        return sorted((self.project_root / "assets" / "charts").glob("*.png"))


def assert_expected_counts(counts: dict[str, int]) -> None:
    failures = {
        name: (counts.get(name), expected)
        for name, expected in EXPECTED_COUNTS.items()
        if name in counts and counts.get(name) != expected
    }
    if failures:
        raise ValueError(f"Dataset count mismatch: {failures}")
