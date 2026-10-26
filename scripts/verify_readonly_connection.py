"""Verify the pooled public-app connection and its enforced restrictions."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from urllib.parse import urlparse

import psycopg

ROOT = Path(__file__).resolve().parents[1]
ROLE = "gchspfam_webapp_reader"


def configured_url() -> str:
    path = ROOT / ".streamlit" / "secrets.toml"
    if not path.is_file():
        raise RuntimeError("The Git-ignored .streamlit/secrets.toml file does not exist.")
    value = tomllib.loads(path.read_text(encoding="utf-8")).get("database", {}).get("url")
    if not value:
        raise RuntimeError("The database.url value is missing from .streamlit/secrets.toml.")
    return str(value).replace("postgresql+psycopg://", "postgresql://", 1)


def rejected(connection: psycopg.Connection, statement: str) -> bool:
    connection.execute("BEGIN")
    try:
        connection.execute(statement)
    except psycopg.errors.InsufficientPrivilege:
        return True
    finally:
        # Even an unexpectedly permitted probe must never persist.
        connection.rollback()
    return False


def main() -> int:
    url = configured_url()
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    preflight = {
        "configured_role": parsed.username or "",
        "expected_role_in_url": parsed.username == ROLE,
        "password_present": parsed.password is not None and parsed.password != "",
        "pooled_hostname": "-pooler" in hostname,
        "sslmode_required": parsed.query.lower().find("sslmode=require") >= 0,
    }
    if not all(value for key, value in preflight.items() if key != "configured_role"):
        print(json.dumps({"overall_status": "FAIL", "preflight": preflight}, indent=2))
        return 1

    with psycopg.connect(url, autocommit=True) as connection:
        user, ssl, candidates, selected, matched = connection.execute(
            """
            select
                current_user,
                (select ssl from pg_stat_ssl where pid=pg_backend_pid()),
                (select count(*) from research.candidate_results),
                (select count(*) from research.selected_plans),
                (select count(*) from research.matched_framework_results)
            """
        ).fetchone()
        role_is_expected = user == ROLE
        # Never issue permission-probe statements through an unexpectedly
        # privileged connection, such as an accidentally supplied owner URL.
        insert_rejected = role_is_expected and rejected(
            connection,
            "insert into research.validation_summary (name,payload) values ('permission_probe','{}')",
        )
        create_rejected = role_is_expected and rejected(
            connection, "create table research.permission_probe (id integer)"
        )
        privileges = connection.execute(
            """
            select
                has_schema_privilege(current_user, 'research', 'USAGE'),
                has_schema_privilege(current_user, 'research', 'CREATE'),
                has_table_privilege(current_user, 'research.selected_plans', 'SELECT'),
                has_table_privilege(current_user, 'research.selected_plans', 'INSERT')
            """
        ).fetchone()

    checks = {
        "observed_role": str(user),
        "expected_role": role_is_expected,
        "pooled_hostname": preflight["pooled_hostname"],
        "sslmode_required": preflight["sslmode_required"],
        "server_side_ssl_observation": bool(ssl),
        "candidate_count": int(candidates) == 2_592_000,
        "selected_count": int(selected) == 15_552,
        "matched_count": int(matched) == 5_184,
        "schema_usage": bool(privileges[0]),
        "schema_create_denied": not bool(privileges[1]),
        "select_allowed": bool(privileges[2]),
        "insert_privilege_denied": not bool(privileges[3]),
        "insert_statement_rejected": insert_rejected,
        "create_statement_rejected": create_rejected,
    }
    required = {
        key: value for key, value in checks.items() if key not in {"observed_role", "server_side_ssl_observation"}
    }
    status = "PASS" if all(required.values()) else "FAIL"
    print(json.dumps({"overall_status": status, "checks": checks}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
