# Phase 816 — Consumer-Side Runtime Bundle Release Gate

Date: 2026-10-22

## Implemented

- Added `scripts/verify_runtime_bundle_release.py`, a fail-closed consumer API that validates actual bundle bytes and manifest, computes the content digest, loads a strict attestation document, and verifies Ed25519 signature, trusted key, issuer/subject allowlists, source revision, producer run ID, artifact ID/name/service digest and freshness.
- Added tests proving valid statements pass and wrong key/issuer/subject, source SHA, producer run ID, artifact ID/digest, tampered bundle/signature and missing trust root are rejected.
- The gate requires the caller to provide producer run/artifact metadata obtained independently from a trusted API/source; data copied only from the attestation JSON is not authoritative.
 
## Not yet connected to production evidence runtime

This is a standalone release-verification API and is not proof that a deployed service invokes it. Production integration requires a reviewed deployment/bootstrap entrypoint, provisioned public trust-root material, actual signing key configuration, and a release/deployment rehearsal.

PR #97 remains OPEN / DRAFT / UNMERGED pending independent review and remaining production gates. **Production HOLD.**
