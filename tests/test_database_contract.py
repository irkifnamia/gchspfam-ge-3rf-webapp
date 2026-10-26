from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_schema_contains_all_authoritative_tables():
    schema = (ROOT / "db" / "schema.sql").read_text(encoding="utf-8").lower()
    for table in (
        "research.candidate_results",
        "research.selected_plans",
        "research.matched_framework_results",
        "research.fixed_plan_oc",
        "research.validation_summary",
        "research.import_manifest",
        "research.analysis_units",
        "research.candidate_fact",
    ):
        assert table in schema


def test_candidate_storage_is_normalized_without_reducing_precision():
    schema = (ROOT / "db" / "schema.sql").read_text(encoding="utf-8").lower()
    assert "create or replace view research.candidate_results" in schema
    assert "double precision" in schema
    assert "real " not in schema
    assert "primary key (analysis_unit_id, candidate_g)" in schema


def test_public_app_role_is_select_only():
    role = (ROOT / "db" / "readonly_role.sql.example").read_text(encoding="utf-8").lower()
    assert "grant select" in role
    assert "grant insert" not in role
    assert "grant update" not in role
    assert "grant delete" not in role
