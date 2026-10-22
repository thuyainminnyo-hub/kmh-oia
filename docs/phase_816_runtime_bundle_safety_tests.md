# Phase 816 — Consumer-Side Runtime Bundle Release Gate

Date: 2026-10-21

## Implemented

- Added `scripts/verify_runtime_bundle_release.py`, a fail-closed consumer API that validates bundle bytes and the internal manifest, loads strict attestation JSON and checks Ed25519 signature, trusted public key, issuer/subject allowlists, source revision, producer run ID, artifact ID/name/service digest and freshness.
- Added regression tests that accept a valid signed bundle and reject wrong key/issuer/subject, source SHA, producer run ID, artifact ID/digest, tampered bundle/signature and a missing trust root.
- The caller must obtain producer run/artifact metadata from a trusted API/source and pass those observations into this gate. Untrusted envelope values alone are not authoritative.

## Verification boundary

This consumer gate is standalone and not yet wired into `ProductionEvidenceRuntime` or a deployed bootstrap process. No production public key, GitHub Environment configuration, production signing run or deployment has been verified. The trusted producer workflow must execute on `main` to create a real eligible artifact/run.

PR #97 remains OPEN / DRAFT / UNMERGED. **Production HOLD.**



## Phase 817 — Production Bootstrap Integration Contract

- Extended `ProductionEvidenceRuntimeConfig` to require the release bundle path, signed attestation path, expected source SHA, producer run ID, artifact ID/name/service digest, trusted public-key map, and exact issuer/subject allowlists.
- `build_production_evidence_runtime()` now calls the consumer release gate before creating the SQLite replay store or the live runtime bridge. Missing keys/configuration or invalid bundle/signature/provenance aborts startup.
- Production public keys remain external deployment configuration; no private or public production key is embedded in repository code. This verifies the supplied release bundle only; it does not prove the deployed files are those bytes unless deployment/bootstrap actually uses the verified artifact and records a deployment receipt.
- **Production HOLD** until real trusted run/artifact data and public keys are provisioned, and deployment plus rollback evidence and independent review are verified.
