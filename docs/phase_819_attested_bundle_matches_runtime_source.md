# Phase 819 — Attested Bundle Must Match Runtime Source Tree

Date: 2026-10-22

## Change

The consumer release verifier now compares the signed runtime source bundle’s per-file manifest against the configured runtime source root before trusting release metadata. The source root must contain `src/` and `requirements.txt`; all regular `src/` files and `requirements.txt` must have exactly the same relative paths and SHA-256 values as the attested bundle. Symlinks and non-regular items are rejected; generated `__pycache__`, `.pyc` and `.pyo` are excluded.

`ProductionEvidenceRuntimeConfig` requires `runtime_source_root` whenever release bundle verification is activated, and the factory validates the bundle/attestation/source tree before constructing the live bridge or creating the SQLite receipt replay store.

## Verification boundary

Regression tests check both the valid matching tree and a source file modified after packaging/signing; the mismatch must fail before the replay database is created. CI on the final commit must pass before Phase 819 is considered verified.

This verifies on-disk source consistency against the signed artifact. It does not dynamically install/execute the bundle, prove which Python modules were already imported into memory, validate external provider authenticity, or prove production deployment. External GitHub Environment reviewers/secrets, deployment, rollback rehearsal and independent human review remain outstanding.

PR #97 stays OPEN / DRAFT / UNMERGED. **Production HOLD.**
