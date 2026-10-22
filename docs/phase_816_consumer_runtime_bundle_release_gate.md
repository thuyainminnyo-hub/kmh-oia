# Phase 816 — Consumer-Side Runtime Bundle Release Gate

Date: 2026-10-22

## Implemented

- Added `scripts/verify_runtime_bundle_release.py`, a fail-closed consumer API that validates bundle bytes and the internal manifest, computes the content digest, loads a strict attestation, and verifies the Ed25519 signature, trusted key, issuer/subject allowlists, source revision, producer run ID, artifact ID/name/service digest and freshness.
- Producer run/artifact expected fields must be fetched independently from a trusted source; fields copied only from an untrusted attestation are not authoritative.

## Follow-up integration

- `ProductionEvidenceRuntimeConfig` and `build_production_evidence_runtime` already call release validation before constructing the bridge or opening the SQLite replay store.
- Phase 819 tightens that integration: the configured runtime source tree must match the signed bundle’s `src/` files and `requirements.txt` byte-for-byte (excluding generated Python bytecode/cache). A mismatch rejects startup before creating the store.
- The factory verifies the deployed source tree on disk; it does not dynamically install or execute the source bundle, and the check does not prove a real production deployment occurred.

**Production HOLD.** PR #97 remains OPEN / DRAFT / UNMERGED pending independent human review, external trust configuration and release evidence gates.
