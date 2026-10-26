# GChSPFAM-GE-3RF Research Analytics

Interactive, read-only exploration of the validated GChSPFAM-GE-3RF consumer-risk-restriction results.

The application does **not** select new plans or alter the research methodology. It displays the authoritative Stage 7--10 datasets produced by the separate `gchspfam-ge-3rf-results` project.

## Architecture

- **Codex**: development, testing, migrations, and review.
- **GitHub**: public source repository and continuous integration.
- **Streamlit**: interactive web application and public deployment.
- **Neon PostgreSQL**: production query layer for all 2,592,000 candidate records and the research-ready analytical datasets.

The app supports two data backends:

1. `local`: reads the validated sibling results project without modifying it.
2. `neon`: queries the production PostgreSQL schema with a read-only connection.

## Local setup

```powershell
python -m venv .venv --system-site-packages
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:GCHSPFAM_RESULTS_DIR = "C:\path\to\gchspfam-ge-3rf-results"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If the results project is a sibling named `gchspfam-ge-3rf-results`, the environment variable is optional.

## Neon configuration

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add the **read-only pooled** Neon connection string locally. Never commit the real secrets file.

```toml
[database]
url = "postgresql+psycopg://..."
```

The administrative connection used by the importer is supplied separately through `NEON_DATABASE_URL`. The public app must use `NEON_READONLY_DATABASE_URL` or the read-only value in Streamlit secrets.

## Database preparation

```powershell
$env:NEON_DATABASE_URL = "postgresql://..."
.\.venv\Scripts\python.exe scripts\load_neon.py --apply-schema
.\.venv\Scripts\python.exe scripts\load_neon.py --all
.\.venv\Scripts\python.exe scripts\validate_neon.py
```

The candidate import is partition-aware and resumable. Each of the 48 source Parquet files is recorded in `research.import_manifest` with its SHA-256 digest and row count.

See [Architecture](docs/ARCHITECTURE.md) for the lossless normalized candidate
storage design and [Deployment](docs/DEPLOYMENT.md) for the credential-safe
Neon, GitHub, and Streamlit release procedure.

## Quality checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

## Research safeguards

- The results project is read-only.
- No producer-risk constraint is introduced.
- Risk sums are descriptive and are never optimized.
- Own-risk and common-risk quantities remain explicitly distinguished.
- Full numerical precision is retained in the database and downloads.
- AUOIR and MAM are intentionally excluded.

