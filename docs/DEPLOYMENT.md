# Secure deployment runbook

## 1. Local verification

From the webapp directory:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```

With no database secret configured, the app reads the validated sibling
`gchspfam-ge-3rf-results` project in read-only mode.

## 2. Neon administrative import

Use the direct (non-pooled) Neon connection string for this one-time bulk
load. Do not paste it into tracked source files, GitHub, or chat. Either set it
only in the current terminal, or copy `.streamlit/admin_secrets.toml.example`
to `.streamlit/admin_secrets.toml` and edit the ignored local copy in VS Code.

```powershell
$env:NEON_DATABASE_URL = "postgresql://ADMIN_USER:ADMIN_PASSWORD@DIRECT_HOST/neondb?sslmode=require"
.\.venv\Scripts\python.exe scripts\load_neon.py --all
.\.venv\Scripts\python.exe scripts\validate_neon.py
.\.venv\Scripts\python.exe scripts\verify_neon_source_parity.py
Remove-Item Env:\NEON_DATABASE_URL
```

The local administrator secret file is also accepted by both commands above.
It is separate from the read-only application secret.

The loader commits every candidate partition separately. A rerun checks the
stored SHA-256 and row count, then skips each completed partition.

After validation, inspect database size in Neon or with:

```sql
select pg_size_pretty(pg_database_size(current_database()));
select relname, pg_size_pretty(pg_total_relation_size(oid))
from pg_class
where relnamespace = 'research'::regnamespace
order by pg_total_relation_size(oid) desc;
```

## 3. Read-only application role

Run the idempotent provisioning script with the administrative connection:

```powershell
.\.venv\Scripts\python.exe scripts\provision_readonly_role.py
```

It creates `gchspfam_webapp_reader` without a password, grants SELECT-only
access, and verifies that INSERT, UPDATE, DELETE, CREATE, and TRUNCATE are
unavailable. Because this is a SQL-created role, Neon Console may report
`cannot update password for role without password` if its reset dialog is
used. Set the initial password once through an administrator SQL connection,
then use the role's pooled connection string. Do not use the owner connection
in Streamlit.

After saving the pooled URL in the ignored `.streamlit/secrets.toml`, verify
both the connection identity and enforced permissions:

```powershell
.\.venv\Scripts\python.exe scripts\verify_readonly_connection.py
```

The command must report `PASS`. It checks the expected role and authoritative
record counts and safely confirms that real INSERT and CREATE probes are
rejected. It will not issue mutation probes through an unexpectedly privileged
connection.

## 4. GitHub

Create the public repository `irkifnamia/gchspfam-ge-3rf-webapp`, then push the
local `main` branch. Never commit `.streamlit/secrets.toml`, `.env`, database
URLs, passwords, or the authoritative candidate Parquet files.

The included GitHub Actions workflow installs dependencies, runs Ruff, and
runs pytest on every push and pull request.

## 5. Streamlit Community Cloud

1. Create an app from `irkifnamia/gchspfam-ge-3rf-webapp` and select `app.py`.
2. In app secrets, add only the pooled read-only URL:

   ```toml
   [database]
   url = "postgresql+psycopg://READ_ONLY_USER:PASSWORD@POOLED_HOST/neondb?sslmode=require"
   ```

3. Deploy privately for verification, exercise all pages, and confirm the
   Validation page reports the authoritative counts and identity checks.
4. Make the Streamlit application public only after those checks pass.

Official references:

- Streamlit secrets: <https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management>
- Streamlit Community Cloud: <https://docs.streamlit.io/deploy/streamlit-community-cloud>
- Neon compute and pooled connections: <https://neon.com/docs/manage/endpoints/>
