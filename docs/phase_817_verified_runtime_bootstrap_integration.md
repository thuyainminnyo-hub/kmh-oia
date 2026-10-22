# Phase 817 — Verified Runtime Bootstrap Integration

Date: 2026-10-22

## Implementation

- Added `src/verified_production_evidence_runtime.py` with `build_verified_production_evidence_runtime(...)`.
- This bootstrap verifies the actual source-bundle bytes, embedded source SHA, manifest, Ed25519 attestation, configured trusted public-key map, exact issuer/subject allowlists, producer run ID, artifact ID/name and artifact-service digest BEFORE constructing `LiveRuntimeBridge`.
- Added integration tests for valid attestation, wrong source SHA, wrong artifact ID, wrong public-key trust root and tampered bundle. These use ephemeral test keys only; no production private key is stored or used.
- Producer run/artifact values must be fetched from GitHub's trusted API by the deployment/bootstrap caller. This function intentionally does not perform network requests or infer remote truth from the attestation alone.

## Boundaries

This wiring is an explicit, opt-in verified bootstrap path. The legacy `build_production_evidence_runtime(...)` factory remains for provider-receipt/evidence use and does not itself verify the bundle. Deployments must adopt the verified bootstrap path and provision public trust roots securely; CI alone does not prove adoption or deployment.

**Production HOLD.** PR #97 remains OPEN / DRAFT / UNMERGED pending exact-head CI, independent review, production trust-root provisioning, deployment proof and rollback rehearsal.
