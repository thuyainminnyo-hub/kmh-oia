# Phase 03.01 — Read-only Evidence-based Recovery Planner

**Status:** Planner and three focused regression tests committed; latest CI pending.
**Date:** 2026-11-10
**Branch:** `phase-02-71/midi-golden-fixtures`

## Research rationale

Crash-recovery research distinguishes crash-point exploration from recovery correctness. B3/CrashMonkey tests crash states against consistency properties; 2026 MC3 work extends model checking to full-stack filesystem features. These support a layered approach: application process-kill tests, read-only recovery evidence inspection, and later filesystem/VM-level crash testing.

References:
- https://www.usenix.org/conference/osdi18/presentation/mohan
- https://github.com/utsaslab/crashmonkey
- https://ieeexplore.ieee.org/abstract/document/11645445/
- https://m.mathnet.ru/php/archive.phtml?jrnid=tisp&option_lang=eng&paperid=1121&wshow=paper

## Implementation

Added `plan_ingest_recovery(workspace)`, which reads pending promotion journals and validates candidate Bags without changing files.

For each journal it:
1. Checks journal schema, state, object ID, SHA-256 syntax, and byte length.
2. Constrains accepted path to `accepted/<object_id>` and staging path to a safe relative path under `staging/`.
3. Rejects path traversal and symlink traversal.
4. Runs manifest path preflight and BagIt validation.
5. Re-hashes `data/source/original.mid` and compares digest and byte length with the journal.
6. Classifies verified accepted Bag, verified staging Bag, or no matching valid Bag.
7. Emits a proposed action for operator review only; it does not finalize receipts, move Bags, remove journals, or release locks.

Proposed classifications:
- `accepted_bag_verified_receipt_reconciliation_required`
- `staged_bag_verified_promotion_not_completed`
- `no_matching_valid_bag_found`
- `journal_or_path_invalid`

Regression tests added:
- verified accepted Bag yields receipt-reconciliation proposal and no filesystem mutation;
- tampered accepted payload is not accepted as matching evidence;
- traversal in journal staging path is rejected.

Commits:
- planner: `a0f0d9102d657d04fc588ba81b276378c633e107`
- accepted/staging path hardening: `17509498f558b63f2c9a1aa3fdf1e010a0e7bf42`
- planner tests: `4f292cc47a58b73f216b83b3e4e615e561bea2a1`
- missing staging traversal correction: `fc98309c4f4ff5d8f8ddc2aad1248b1ab664f387`

## Verification state

- Phase 03.00 subprocess crash test passed on Linux and Windows on commit `60d6f3f...`: 27 targeted tests per platform; 5 pinned LOC fixtures per platform; full OIA test suite 640 tests passed.
- Planner commits are newer. Exact-commit CI for `fc98309...` is queued at the time of this record; no planner-test PASS is claimed yet.
- The planner is read-only and emits proposals only. It does not implement reconciliation.
- Application process termination is not power loss, kernel crash, or block-device crash consistency.
- No full RFC 8493, PREMIS, OCFL conformance, independent replica recovery, rights clearance, or production readiness is claimed.
- Gate A remains OPEN / NOT CLOSED; PR #217 remains OPEN / DRAFT.

## Next steps

1. Inspect exact-commit CI and planner test logs.
2. Add tests for valid staging Bag, unreadable/corrupt journal, symlink accepted/staging path, duplicate journal/object conflict, and missing payload.
3. Design an operator-approved reconciliation command with explicit idempotency and audit receipt semantics.
4. Add reservation liveness protocol using process, host, and boot identity; do not expire by age alone.
5. Plan VM/block-device crash tests on supported Linux filesystems for power-loss claims.