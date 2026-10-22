# Phase 817 — Default-Deny Signed Release Startup Gate

Date: 2026-10-22

## Changed

- `ProductionEvidenceRuntimeConfig.require_signed_release_bundle` defaults to `True`.
- Production runtime config validation now rejects startup when release bundle metadata is wholly absent, before the SQLite replay store or execution bridge is created.
- All release metadata remains all-or-nothing and requires explicit trusted public keys, issuer allowlist, subject allowlist, exact artifact name, expected source SHA, producer run ID, artifact ID and artifact-service digest.
- Existing local/unit test scenarios explicitly opt out using `require_signed_release_bundle=False`, making the exception visible in code instead of relying on an implicit permissive default.
- Added a regression test verifying default startup fails and does not create the replay database when signed provenance is missing.
- Updated Phase 816 documentation to reflect that the verification API is called by the production runtime factory; external trust setup/deployment remain unverified.

## Verification boundary

CI must pass on the exact Phase 817 commit. This test verifies fail-closed startup behavior, not live signing, GitHub Environment approval, public-key provisioning or production deployment.

PR #97 remains OPEN / DRAFT / UNMERGED pending independent human review. **Production HOLD.**
