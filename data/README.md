# Packaged data

This repository does not duplicate the 2,592,000-row authoritative candidate
dataset. Production candidate records are loaded into Neon from the validated
sibling results project.

`chart_manifest.json` records the filename, byte size, and SHA-256 digest of
each packaged Stage 9 chart. The chart files themselves are under
`assets/charts/`.

`neon_deployment_validation.json` records the post-import database counts,
mathematical identity checks, source-parity evidence, storage size, and
read-only role privilege audit. It contains no credentials.
