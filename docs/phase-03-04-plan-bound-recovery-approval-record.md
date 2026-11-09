# Phase 03.04 — Plan-bound Recovery Approval Record

**Status:** Approval record builder/validator and focused tests committed; exact-commit CI pending.
**Date:** 2026-11-10
**Branch:** `phase-02-71/midi-golden-fixtures`

## Verified baseline

Phase 03.03 test commit `733c7ac7ea814ecf73ed1aa8157456c7ebebb05b` completed:
- Full OIA test suite: 645 tests passed.
- Preservation Gate A: Linux and Windows jobs succeeded; each ran 32 targeted tests and five pinned LOC fixtures (5 passed, 0 failed).
- OIA Validation and MIDI Fixture Integrity succeeded.
- The deterministic plan-digest regression test passed on Linux and Windows.

Documentation commit `b6fb8255e701fb5ad24a2d46ba4d392c61b62cd8` also completed OIA Tests, Preservation Gate A, OIA Validation, and MIDI Fixture Integrity successfully.

## Implementation

Added `build_recovery_approval_record()` and `validate_recovery_approval()`.

Approval record fields:
- schema `kmh.preservation-recovery-approval.v1`
- approval_id
- actor_id (external identity claim)
- exact allowlisted action
- plan_sha256
- journal_sha256
- approved_at
- expires_at

Validation checks:
- canonical plan digest recomputes and matches
- approval is bound to exact current plan and journal digest
- action matches the planner's allowlisted proposed action
- expiry is timezone-aware and has not elapsed
- an injected trusted `authorize_actor(actor_id, action)` callback positively authorizes the action

Added tests:
- valid plan-bound approval with positive authorization
- rejection when authorization provider denies actor
- rejection after plan contents change
- rejection of action not allowed for the planner proposal
- rejection after expiry

Commits:
- approval builder/validator: `13145607ab4267146ffd8b73f8a0b70b6a790c53`
- approval tests: `3a17f942e0be78b231cd2464fe602ee4621d533b`

## Security boundaries

- `actor_id` is a claim, not authenticated identity. Security depends on a trusted external authorization provider; the default is fail-closed when no provider is supplied.
- The approval record is not signed and is not itself an authentication credential.
- No recovery mutation executor is implemented. No receipt finalization, promotion, deletion, or lock release occurs from this feature.
- Expiry is checked, but revocation storage and replay prevention still need design.
- A future executor must recompute the recovery plan immediately before mutation and reject stale approvals; then enforce idempotency and append-only audit evidence.
- Exact-commit CI for approval builder/test commits is pending; do not claim tests pass until run logs are inspected.

## Next steps

1. Verify exact-commit Linux/Windows and full-suite CI.
2. Add approval-record tamper detection/signature or protected append-only storage, nonce/replay prevention, and revocation registry.
3. Define a trusted operator identity/authorization integration and permission matrix.
4. Implement stale-plan revalidation and an idempotency ledger before any recovery mutation.
5. Keep recovery execution disabled until all safety acceptance criteria pass.

PR #217 remains OPEN / DRAFT. Gate A remains open; no production-readiness claim.