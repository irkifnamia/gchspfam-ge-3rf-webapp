# Application architecture

## Separation of concerns

The validated project `gchspfam-ge-3rf-results` remains the authoritative,
read-only research package. This web application does not recompute plans,
change risk definitions, or write to that project.

```text
Validated Stage 6–10 outputs
          |
          +-- local read-only repository (development and verification)
          |
          +-- compact hashed analytics snapshots --> Streamlit app
          |
          +-- resumable loader --> Neon PostgreSQL
                                      |
                                      +-- read-only candidate queries --> Streamlit app
GitHub --> CI checks --> Streamlit Community Cloud deployment
```

## Data layers

- `selected_plans`: 15,552 framework-selected records.
- `matched_framework_results`: 5,184 matched prior–scenario units.
- `fixed_plan_oc`: 15,552 fixed-plan OC evaluations.
- `analysis_units`: the 5,184 invariant prior–scenario metadata records.
- `candidate_fact`: all 2,592,000 candidate records in normalized form.
- `candidate_results`: a view reconstructing the authoritative 31-column
  candidate dataset without loss of precision.
- `import_manifest`: SHA-256, source row count, imported row count, status, and
  timestamp for each source partition.

The normalization stores metadata such as `p1`, `p2`, Beta parameters, and
design factors once per prior–scenario combination instead of 500 times. All
risk quantities remain PostgreSQL `double precision` values. The candidate
fact primary key is `(analysis_unit_id, candidate_g)`.

The three compact analytical tables are also packaged as immutable Parquet
snapshots. This makes overview, comparison, OC, and sensitivity pages local
reads after deployment. The full candidate table is not packaged: the app
queries one 500-row trace from Neon and retains up to 32 recent traces in a
bounded process-level cache.

## Research safeguards

- Candidate and selected-plan keys are unique.
- Every displayed selected plan comes from the validated Stage 7 datasets.
- Candidate exploration queries one 500-row prior–scenario trace at a time.
- Producer risks and risk sums are display-only measures.
- The public connection is a separate read-only database role.
- Administrative credentials are used only for schema creation and import.

## Capacity note

The 48 source Parquet files occupy approximately 125 MiB because Parquet is
compressed and columnar. A denormalized PostgreSQL table with several wide
indexes would be substantially larger. The normalized schema is deliberately
used to reduce repeated metadata and index storage. After import, verify the
actual Neon project size before public deployment. Neon documented a 1 GB
per-project Free-plan storage allowance in October 2026:
<https://neon.com/blog/neon-free-plan-1-gb-per-project>.
