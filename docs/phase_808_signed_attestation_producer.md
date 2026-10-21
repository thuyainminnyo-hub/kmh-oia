# Phase 808 — Signed Attestation Producer and Strict Reader

Date: 2026-10-21

## Delivered
Added `scripts/create_runtime_artifact_attestation.py` to measure the built classifier/policy bytes and create an Ed25519-signed attestation. The private Ed25519 seed is read only from `KMH_OIA_ATTESTATION_PRIVATE_KEY_B64`; key ID, issuer and exact subject come from release environment configuration. The helper never writes private-key bytes to disk or prints them.

Added `src/runtime_artifact_io.py` to serialize signed statements to a new JSON file without overwriting existing evidence and to strictly parse JSON with an exact supported field set, digest validation, schema version, and full source revision validation. Signature authenticity remains the verifier's responsibility.

## Verification added
- Producer output passes the existing Ed25519 verifier against the actual artifact byte digests.
- Mutating an artifact after signing changes its digest and invalidates the signed expected identity.
- Missing/malformed key, invalid source revision, wildcard subject, empty artifact, existing output, and unexpected JSON fields fail closed.
- Unit tests use ephemeral keys only; no real private key or production trust root is checked into the repository.

## Deployment boundary
This utility is not yet attached to a protected build/release workflow because actual production artifact build paths and GitHub Environment/secret configuration have not been supplied. Production must store the private key in an access-restricted release environment, keep the matching public key in the deployment trust-root allowlist, bind the source revision to the immutable build checkout, and independently review key rotation/revocation. No production attestation has been generated or deployed by this code change.

**Decision: Production HOLD.**

PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/97
