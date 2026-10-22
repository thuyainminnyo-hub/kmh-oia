# Phase 816 — Consumer-Side Runtime Bundle Release Gate

Date: 2026-10-22

## Implemented

- Added `scripts/verify_runtime_bundle_release.py`, a fail-closed consumer API that validates actual bundle bytes and manifest, computes the content digest, loads a strict attestation document, and verifies Ed25519 signature, trusted key, issuer/subject allowlists, source revision, producer run ID, artifact ID/name/service digest and freshness.
- Added tests proving valid statements pass and wrong key/issuer/subject, source SHA, producer run ID, artifact ID/digest, tampered bundle/signature and missing trust root are rejected.
- The gate requires the caller to provide producer run/artifact metadata obtained independently from a trusted API/source; data copied only from the attestation JSON is not authoritative.
 
## Production startup integration and remaining gate

`ProductionEvidenceRuntimeConfig` calls the release-verification API before creating the replay store or execution bridge. Phase 817 makes this verification required by default; no-bundle startup must explicitly set `require_signed_release_bundle=False`, which is intended only for isolated local/unit-test setups. Release fields are all-or-nothing and require a provisioned trusted public-key map and issuer/subject allowlists.

This factory-level startup check is tested, but no live production service has been shown invoking this factory with the actual production bundle or provisioned trust root. Actual signing secrets, protected Environment reviewer rules, real provider authenticity, deployment/release rehearsal and rollback evidence remain unverified. The signed release attestation is not proof of deployment.

PR #97 remains OPEN / DRAFT / UNMERGED pending independent review and remaining production gates. **Production HOLD.**
