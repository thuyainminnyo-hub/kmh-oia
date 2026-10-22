# Phase 817 — Runtime Factory Integration Verification

Date: 2026-10-22

## Source audit

Inspected `src/production_evidence_runtime.py`. `ProductionEvidenceRuntimeConfig.validate_release_bundle()` invokes `verify_runtime_bundle_release(...)`, and `build_production_evidence_runtime()` calls it before creating `SQLiteReceiptReplayStore` or `LiveRuntimeBridge`. Release verification is enabled by default; test-only calls must explicitly disable it.

## Regression coverage added

- Builds a real deterministic bundle in a temporary directory, signs its digest with an ephemeral test-only Ed25519 key and confirms the config gate returns pinned source/run/artifact metadata.
- Confirms the factory starts only after a valid test-signed release, then opens the durable replay store.
- Mutates the attestation so signature validation fails and confirms the evidence SQLite file is not created.
- No production private keys, real issuer identities, or fake release artifacts are committed.

## Verification boundary

This is integration-level test coverage using generated test keys; it is not a live production key exercise or deployed service startup. The production signer environment/key provisioning and independent release review remain separate controls. The factory verifies the local attested source bundle, but it does not dynamically replace imported Python modules from the bundle and does not itself query GitHub's API; producer metadata must be fetched and pinned by trusted deployment automation before values are provided.

PR #97 remains OPEN / DRAFT / UNMERGED. **Production HOLD.**
