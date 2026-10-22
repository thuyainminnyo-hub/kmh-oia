# Phase 816 — Consumer-Side Runtime Bundle Release Gate

Date: 2026-10-22

## Implemented

- Added `scripts/verify_runtime_bundle_release.py`, a fail-closed consumer API that validates the actual bundle bytes and internal manifest, computes the content digest, loads a strict attestation, and verifies Ed25519 signature, trusted key, exact issuer/subject allowlists, source revision, producer run ID, artifact ID/name/service digest and freshness.
- Added tests proving a valid statement passes and wrong keys/issuer/subject, source SHA, producer run ID, artifact ID/digest, tampered bundle/signature and missing trust root are rejected.
- Producer run/artifact metadata must be fetched independently from a trusted API/source; untrusted attestation fields are not authoritative expected values.

## Integration boundary

The existing LiveRuntimeBridge/ProductionEvidenceRuntimeConfig handles provider receipts and execution evidence; it does not load release bundles into the deployed OIA runtime. This is a standalone release verification API, not proof the deployed service invokes it. Production integration still requires a reviewed deployment/bootstrap entrypoint and provisioned public trust-root material.

**Production HOLD.** PR #97 remains OPEN / DRAFT / UNMERGED pending independent review and production evidence gates.
