# Phase 812 — Immutable Build Artifact Handoff & Provenance Verification

Date: 2026-10-21

## Phase 812 implementation

Added `scripts/validate_build_artifact_provenance.py` and `tests/test_build_artifact_provenance.py`. The validator checks an exact-field provenance envelope binding repository, approved workflow path, successful producer run, full source SHA, run ID, artifact ID/name and SHA-256 service digest to expected values.

## Phase 813 integration

The protected signing workflow now requires producer run ID, workflow path, source SHA, immutable artifact ID, exact artifact name, GitHub artifact digest and expected release SHA. Preflight queries GitHub's Actions run and artifact APIs, requiring a completed successful run with the exact workflow path, source SHA, repository, main branch and push event.

After preflight and the protected Environment gate, the signer downloads by artifact ID, requires exactly two non-empty files (`classifier.bin`, `policy.bin`), verifies the downloaded ZIP digest, then signs the measured bytes. The attestation source SHA and build run ID represent the verified producer.

## Limits and decision

The expected producer workflow path is `.github/workflows/trusted-runtime-build.yml`; artifact name is `kmh-oia-runtime-bundle`. The producer workflow is not yet implemented, so the signing gate intentionally fails closed until it exists. Static CI does not prove live API behavior, production environment configuration or deployment.

PR #97 remains OPEN / DRAFT / UNMERGED pending independent review and production gates. **Production HOLD.**
