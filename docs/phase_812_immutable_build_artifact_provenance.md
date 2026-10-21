# Phase 812 — Immutable Build Artifact Handoff & Provenance Verification

Date: 2026-10-21

## Source inspection finding

At the inspected PR #97 head `8082ac9d4117678acb9c25056e9389dbadb5a2e8`, `.github/workflows/production-runtime-artifact-attestation.yml` checks input paths inside a checkout of the release source and passes the current signing run's `GITHUB_RUN_ID` as `build_run_id`. This is not an immutable producer-artifact handoff. A signing run ID does not independently identify the build run that produced the signed bytes.

## Phase 812 implementation

Added `scripts/validate_build_artifact_provenance.py`, a fail-closed validator for a versioned, exact-field provenance envelope. It requires:

- exact repository and explicitly allowlisted producer workflow path;
- successful producer run and positive run attempt;
- full 40-character source SHA equal to the expected release SHA;
- producer run ID bound consistently to `run_id` and `producer_run_id`;
- exact artifact ID, artifact name, and SHA-256 artifact service digest matching independently supplied expected values;
- no missing or extra fields, no placeholder allowlist, and canonical numeric identifiers.

Added `tests/test_build_artifact_provenance.py` with positive and negative contract tests for failed runs, unapproved workflows, missing/extra fields, SHA/run/artifact mismatches, malformed IDs/digests, and missing allowlist.

## Important trust boundary

This validator checks a metadata envelope against values supplied by a trusted caller. It does **not** fetch GitHub Actions run/artifact metadata, authenticate an artifact download, validate GitHub's artifact digest itself, verify signatures, or prove the producer workflow is configured/protected. Callers must query GitHub's API independently, require completed/successful workflow run, verify the actual run's workflow path and source SHA, fetch the artifact only by the verified artifact ID, and hash downloaded bytes against the artifact service digest before trusting the envelope.

The existing signing workflow remains unchanged and must not be regarded as using this validator yet. Do not claim the trusted build handoff is end-to-end complete until the approved producer workflow and exact artifact contract are connected, independently reviewed, and tested against actual GitHub artifact metadata.

## Verification and release decision

CI must pass on the exact new head before this phase is marked verified. This repository-level contract is a guardrail, not production deployment evidence.

PR #97 remains OPEN / DRAFT / UNMERGED pending independent human review and production verification. Runtime provider authenticity, protected Environment settings, production trust-root configuration, target-host deployment evidence, migration/rollback rehearsal, and release sign-off remain outstanding.

**Decision: Production HOLD.**
