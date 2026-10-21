# Phase 805 — Verified Runtime Artifact Loader Integration

Date: 2026-10-21

## Implementation
Added `src/runtime_artifact_loader.py`. It measures classifier and policy artifact bytes, passes the measured SHA-256 values to the configured attestation verifier, and invokes neither format-specific loader unless verification returns literal `True`. Loader callbacks receive the immutable byte snapshots, not file paths. The returned bundle preserves the objects and byte payloads together and can re-check payload hashes and signed attestation before learning admission.

`TrustedDecisionLearningService` now requires a `VerifiedRuntimeArtifacts` bundle for admission. It binds its classifier object and attestation verifier to the bundle, rechecks the stored byte hashes and signed attestation, and fails closed when the bundle is missing, mismatched, or invalid. Unit-test fixtures were adapted to use the loader interface; fake verifiers remain test-only.

## Verification
- Loader tests cover exact byte handoff, no loader invocation on digest/provenance rejection, issuer rejection, path snapshot loading, and empty payload rejection.
- Learning-service tests cover missing bundle fail-closed and mutation of stored bytes.
- Exact-head CI results to be recorded after runs complete.

## Trust boundary / remaining work
This is an application wiring contract, not proof that any production classifier/policy artifact file exists or that a concrete production format loader has been configured. Production public keys, signer pipeline, key rotation/revocation, actual policy-engine integration, independent review, provider authenticity, migration/rollback, deployment, and release sign-off remain outstanding.

**Decision: Production HOLD.**

PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/97
