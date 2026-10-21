# Phase 814 — Canonical Artifact Trust Contract Reconciliation

Date: 2026-10-21

Unified the signer allowlist and provenance fixture path to `.github/workflows/trusted-build.yml` and added path-drift regression coverage. A recursive repository-tree inspection found no classifier/policy binaries; `src/autonomy_policy.py` is Python source, not a compiled classifier.

Phase 815 addresses that artifact-shape mismatch by defining the actual release input as a deterministic source bundle built from `src/` and `requirements.txt`, with a source-revision marker and SHA-256 manifest. This is a source release artifact, not a compiled classifier and not evidence of deployment.

**Production HOLD** remains unchanged.
