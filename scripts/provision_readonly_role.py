"""Provision and verify the passwordless read-only Neon application role."""

from __future__ import annotations

import json

import psycopg
from load_neon import database_url
from psycopg import sql

ROLE = "gchspfam_webapp_reader"


def main() -> int:
    with psycopg.connect(database_url(), autocommit=True) as connection:
        database = str(connection.execute("select current_database()").fetchone()[0])
        connection.execute(
            sql.SQL(
                """
                do $$
                begin
                    if not exists (select 1 from pg_roles where rolname = {role_literal}) then
                        execute {create_statement};
                    end if;
                end
                $$
                """
            ).format(
                role_literal=sql.Literal(ROLE),
                create_statement=sql.Literal(f"create role {ROLE} login"),
            )
        )
        connection.execute(
            sql.SQL("revoke all on database {} from {}").format(sql.Identifier(database), sql.Identifier(ROLE))
        )
        connection.execute(
            sql.SQL("grant connect on database {} to {}").format(sql.Identifier(database), sql.Identifier(ROLE))
        )
        connection.execute(sql.SQL("revoke all on schema research from {}").format(sql.Identifier(ROLE)))
        connection.execute(sql.SQL("grant usage on schema research to {}").format(sql.Identifier(ROLE)))
        connection.execute(sql.SQL("revoke all on all tables in schema research from {}").format(sql.Identifier(ROLE)))
        connection.execute(sql.SQL("grant select on all tables in schema research to {}").format(sql.Identifier(ROLE)))
        connection.execute(
            sql.SQL("revoke all on all sequences in schema research from {}").format(sql.Identifier(ROLE))
        )
        connection.execute(
            sql.SQL("revoke all on all functions in schema research from {}").format(sql.Identifier(ROLE))
        )
        connection.execute(
            sql.SQL("alter default privileges in schema research grant select on tables to {}").format(
                sql.Identifier(ROLE)
            )
        )

        privileges = connection.execute(
            """
            select
                has_schema_privilege(%s, 'research', 'USAGE'),
                has_schema_privilege(%s, 'research', 'CREATE'),
                has_table_privilege(%s, 'research.selected_plans', 'SELECT'),
                has_table_privilege(%s, 'research.selected_plans', 'INSERT'),
                has_table_privilege(%s, 'research.selected_plans', 'UPDATE'),
                has_table_privilege(%s, 'research.selected_plans', 'DELETE'),
                has_table_privilege(%s, 'research.selected_plans', 'TRUNCATE')
            """,
            (ROLE, ROLE, ROLE, ROLE, ROLE, ROLE, ROLE),
        ).fetchone()

    names = ("schema_usage", "schema_create", "select", "insert", "update", "delete", "truncate")
    observed = dict(zip(names, map(bool, privileges), strict=True))
    expected = {
        "schema_usage": True,
        "schema_create": False,
        "select": True,
        "insert": False,
        "update": False,
        "delete": False,
        "truncate": False,
    }
    status = "PASS" if observed == expected else "FAIL"
    print(json.dumps({"role": ROLE, "status": status, "privileges": observed}, indent=2))
    print("Set or reset this role's password in Neon before constructing the pooled application URL.")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
