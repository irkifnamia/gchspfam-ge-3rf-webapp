# Packaged data

This repository does not duplicate the 2,592,000-row authoritative candidate
dataset. Production candidate records are queried on demand from Neon.

The compact, immutable research-ready selected-plan, matched-framework, and
fixed-plan OC tables are packaged under `data/analytics/`. They are copied from
the validated sibling results project by `scripts/sync_validated_assets.py`,
with row counts and SHA-256 digests recorded in `data/analytics/manifest.json`.
Serving these small snapshots locally removes repeated 20–40 second database
transfers while retaining Neon for the complete candidate-level data.

`chart_manifest.json` records the filename, byte size, and SHA-256 digest of
each packaged Stage 9 chart. The chart files themselves are under
`assets/charts/`.

`neon_deployment_validation.json` records the post-import database counts,
mathematical identity checks, source-parity evidence, storage size, and
read-only role privilege audit. It contains no credentials.
