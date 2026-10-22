# Phase 816 — Consumer-Side Runtime Bundle Release Gate

Date: 2026-10-22

## Implemented

- Added `scripts/verify_runtime_bundle_release.py` to verify bundle bytes, embedded source revision, per-file manifest hashes and detached Ed25519 provenance.
- Wired optional release bundle verification into `ProductionEvidenceRuntimeConfig` and `build_production_evidence_runtime`. If any release metadata is supplied, the configuration must include all bundle/attestation paths, source SHA, producer run ID, artifact ID/name/service digest, public key trust root, issuer and subject allowlists. Verification runs before the execution bridge and SQLite replay store are constructed.
- Added startup regressions for partial release config and invalid bundle/attestation; invalid release evidence must fail closed before the durable store is created.
- The verifier requires externally observed producer run/artifact metadata and does not fetch GitHub APIs by itself.

## Remaining boundary

The factory still permits legacy/test runtime construction if no release settings are supplied. It is not yet verified that every production deployment entrypoint always supplies the signed-release configuration. No production signing key or real signed release bundle has been provisioned/exercised. External provider authenticity, actual deployment, rollback rehearsal and independent human review remain outstanding.

PR #97 remains OPEN / DRAFT / UNMERGED. **Production HOLD.**
