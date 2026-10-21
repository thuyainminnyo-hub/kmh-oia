# Phase 816 — Consumer-Side Runtime Bundle Release Gate

Date: 2026-10-21

## Implemented

- Added `scripts/verify_runtime_bundle_release.py`, a fail-closed consumer API that validates bundle bytes and the internal manifest, loads strict attestation JSON and checks Ed25519 signature, trusted public key, issuer/subject allowlists, source revision, producer run ID, artifact ID/name/service digest and freshness.
- Added regression tests that accept a valid signed bundle and reject wrong key/issuer/subject, source SHA, producer run ID, artifact ID/digest, tampered bundle/signature and a missing trust root.
- The caller must obtain producer run/artifact metadata from a trusted API/source and pass those observations into this gate. Untrusted envelope values alone are not authoritative.

## Verification boundary

This consumer gate is standalone and not yet wired into `ProductionEvidenceRuntime` or a deployed bootstrap process. No production public key, GitHub Environment configuration, production signing run or deployment has been verified. The trusted producer workflow must execute on `main` to create a real eligible artifact/run.

PR #97 remains OPEN / DRAFT / UNMERGED. **Production HOLD.**
