# Phase 797 — Transactional Trusted Learning Service Integration

## Integrated behavior on this branch
- `TrustedDecisionLearningService` now requires an explicit `SQLiteLearningAdmissionRepository` and routes admitted learning writes through its transaction.
- The service no longer calls `OperatingMemory.record()` for admission writes; this avoids writing the same event to a second JSON-backed store.
- A stable admission key is derived from decision ID, execution ID, and evidence ID.
- A canonical SHA-256 request fingerprint binds decision/execution trace, verified receipt facts, policy version, next command, confidence, and classifier type/version.
- After fresh receipt verification, an identical committed request returns the persisted result before classifying again.
- Reusing the same admission identity with different request content is rejected.
- Admission result, learning record, optional PROPOSED adaptation, and audit event commit together.
- Proposal IDs are tied to the admission key instead of relying only on command ID.

## Tests added/updated
- Existing trust-chain rejection tests remain.
- Successful capture now verifies SQLite persistence instead of expecting the separate JSON memory object to be updated.
- Duplicate retry must return the same stored result with no reclassification or extra database rows.
- Same identity with a changed policy fingerprint must be rejected without extra writes.
- The repository transaction rollback, concurrent idempotency, and restart tests remain enabled.

## Limits and release gates
- The classifier type/version identity is not a complete immutable artifact digest; production should supply an explicit classifier artifact version.
- SQLite here is local-filesystem persistence, not a shared multi-host guarantee.
- Provider authenticity depends on a real configured provider adapter; the test adapter is not production proof.
- JSON-to-SQLite migration, backup/restore drill, target runtime deployment, external execution evidence, and independent review/sign-off are not completed by this integration commit.
- All adaptation proposals remain `PROPOSED`; approval/application are separate governance actions.

**Production remains HOLD** pending exact-head CI, independent review, migration/rollback verification, real provider authenticity, and target deployment evidence.
