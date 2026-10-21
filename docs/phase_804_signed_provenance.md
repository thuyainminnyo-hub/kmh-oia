# Phase 804 — Signed Provenance Verification

Date: 2026-10-21

## Implementation
Added `src/runtime_artifact_attestation.py` with an Ed25519 signature verifier. Trusted raw 32-byte public keys are injected by key ID; issuer and subject allowlists are mandatory. The canonical signed payload includes schema version, key ID, issuer, subject, attestation ID, source revision, CI/build run ID, issuance timestamp, and classifier/policy SHA-256 digests.

Verification rejects unknown keys, unapproved issuers/subjects, invalid source revision, missing metadata, malformed/invalid signatures, wrong expected artifact digests, expired attestations when max age is configured, and timestamps beyond permitted clock skew.

The admission audit/fingerprint now also records provenance key ID, source revision, run ID, timestamp, and a SHA-256 of the signature bytes (not the signature itself). Tests use ephemeral in-memory keys and do not configure any production trust root.

## Dependency and CI
Pinned `cryptography==50.0.2` in `requirements.txt` and added dependency installation to both GitHub Actions workflow files.

## Boundary / remaining gate
The verifier code is implemented and tested but production key provisioning, signing workflow, key rotation/revocation, and wiring to the exact measured bytes that the classifier/policy loader actually consumes still require integration and independent review. Test signing keys are ephemeral. A code verifier existing in the repo does not prove production configuration or runtime deployment.

**Decision: Production HOLD.**

PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/97
