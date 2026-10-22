# Phase 817 — Release Provenance Gate at Production Runtime Factory

Date: 2026-10-22

## Implemented

- Extended `ProductionEvidenceRuntimeConfig` with an explicit runtime bundle, attestation, expected source revision, producer run ID, artifact ID/name/service digest, trusted Ed25519 public keys, issuer and subject allowlists, and maximum attestation age.
- Any release-field activation requires the complete set. Partial metadata, an empty trust-root map, missing issuer/subject allowlists, invalid maximum age, or an unapproved artifact name is rejected.
- `build_production_evidence_runtime` invokes bundle/attestation verification before creating the receipt replay store or execution bridge. Verification failure is converted to a safe, non-sensitive startup error.
- Added factory integration tests for acceptance of a valid signed bundle and startup rejection for tampering, wrong source SHA, and missing trust configuration.

## Boundary

This configuration verifies a local bundle/attestation pair against expected producer/artifact metadata supplied by the deployment caller. The caller must obtain that metadata from a trusted GitHub API result; this factory does not make network requests and does not prove that its caller did so. It also does not automatically execute/import code from the bundle. Provider authenticity, environment protections, secrets/key custody, public-key provisioning, deployment proof, rollback rehearsal, and independent human review remain external gates.

PR #97 remains OPEN / DRAFT / UNMERGED. **Production HOLD.**
