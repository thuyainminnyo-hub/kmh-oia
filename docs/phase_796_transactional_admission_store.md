# Phase 796 — Transactional Learning Admission Store (Prototype)

This branch adds a SQLite-backed persistence primitive for admission idempotency and atomic writes. It is intentionally separate from PR #94.

## Added
- `src/learning_admission_repository.py`: transaction-scoped persistence for admission result, learning record, optional proposal, and audit event.
- `tests/test_learning_admission_repository.py`: now includes eight test cases, including concurrent duplicate requests, injected failures, restart readback, fingerprint conflicts, and proposal governance.

## Current limits
- The existing `TrustedDecisionLearningService` is **not wired** to this repository in this change. Do not treat this branch as end-to-end exactly-once learning.
- The caller must supply a stable, correctly computed idempotency key and canonical request fingerprint. The repository does not decide their semantics.
- External side effects must not happen inside the transaction; use a transactional outbox if post-commit dispatch is needed.
- The earlier head passed CI, including 526 tests; the updated concurrency-test head still needs its own exact-head CI verification.
- The implementation uses SQLite on a local filesystem and does not prove multi-host shared-store semantics.

## Review checklist
1. Validate transaction behavior and concurrency assumptions.
2. Run the targeted test file and full CI on the latest exact head.
3. Wire the service and ensure memory/proposal/audit are not written through a second store.
4. Verify migration and rollback with existing JSON memory.
5. Keep production on HOLD until real provider authenticity, target deployment evidence, and independent review exist.
