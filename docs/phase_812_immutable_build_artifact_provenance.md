# Phase 812 — Immutable Build Artifact Handoff & Provenance Verification

Date: 2026-10-21

## Phase 812 implementation

Added `scripts/validate_build_artifact_provenance.py` and `tests/test_build_artifact_provenance.py`. The validator checks an exact-field provenance envelope binding repository, approved workflow path, successful producer run, full source SHA, run ID, artifact ID/name and SHA-256 service digest to expected values.

## Phase 813 integration

The protected signing workflow requires producer run ID, workflow path, source SHA, immutable artifact ID, exact artifact name, GitHub artifact digest and expected release SHA. Preflight queries GitHub's Actions run and artifact APIs, requiring a completed successful run with the exact workflow path, source SHA, repository, main branch and push event.

## Phase 814 contract reconciliation

The workflow allowlist and provenance fixture now use the same canonical producer path: `.github/workflows/trusted-build.yml`. This resolves the previous path mismatch without claiming that the producer workflow is present.

The repository currently contains no `classifier.bin` or `policy.bin` output and has no approved build step that creates those artifacts. The repository's `src/autonomy_policy.py` is executable source, but it is not itself a compiled or trained classifier artifact. We must not rename source files or manufacture placeholder binaries to bypass the signer.

## Limits and decision

The producer workflow is not yet implemented: `.github/workflows/trusted-build.yml` is the canonical approved path but no file currently exists at that path. The signer intentionally fails closed until the project defines/builds its real classifier and policy outputs and a reviewed producer emits the exact expected bundle. Static CI does not prove live API behavior, production environment configuration or deployment.

PR #97 remains OPEN / DRAFT / UNMERGED pending independent review and production gates. **Production HOLD.**