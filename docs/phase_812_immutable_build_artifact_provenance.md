# Phase 812 — Immutable Build Artifact Handoff & Provenance Verification

Date: 2026-10-21

## Provenance contract

Added `scripts/validate_build_artifact_provenance.py` and its regression tests for immutable producer metadata (repository, approved workflow path, successful producer run, source SHA, run ID, artifact ID/name and artifact service digest).

## Later integration notes

Phase 813 added run/artifact API checks in the protected signer. Phase 814 reconciled the canonical producer workflow path. Phase 815 adds an actual runtime-source bundle producer and switches signing to a dedicated single-bundle digest statement.

The repository does not contain trained/compiled `classifier.bin` or `policy.bin` files, so the current product release artifact is explicitly a deterministic Python runtime source bundle. It is validated against a manifest and source revision; this does not claim it is a compiled model or prove that production deployment has occurred.

**Production HOLD** until independent review, environment/key setup, bundle signer/verifier trust-root provisioning, deployment evidence, rollback rehearsal and release sign-off are complete.
