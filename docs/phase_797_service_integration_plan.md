# Phase 797 — Trusted Learning Service Integration Plan

## Verified current state
- The transactional SQLite repository prototype exists in `src/learning_admission_repository.py`.
- The current `TrustedDecisionLearningService.capture_execution()` still calls `self._memory.record(...)` before calling `self._adaptation_engine.propose(...)`.
- `OperatingMemory.record()` mutates its in-memory list, then separately persists a JSON file.
- `AdaptationEngine.propose()` constructs proposal IDs from `adapt:{command_id}`.
- The exact earlier prototype head passed the test suite and repository validation; the latest PR head is recorded in PR #97.

## Integration contract
1. Preserve every current fail-closed validation, receipt verification, attribution check, and classifier evidence check. No persistence must occur before all checks pass.
2. Introduce one application-level admission repository dependency into `TrustedDecisionLearningService`.
3. Create a stable admission key from immutable execution identity (at minimum execution ID plus evidence/decision identity), and compute the request fingerprint from canonicalized verified inputs and policy version. Reject key reuse with a mismatching fingerprint.
4. Construct the learning-record payload and optional adaptation proposal as data before any persistent mutation.
5. Commit admission result, learning record, optional PROPOSED proposal, and audit event through one repository transaction. The service must not also call JSON memory persistence for the same admission.
6. For a completed duplicate request, return the persisted original result and do not classify again or create a second learning effect.
7. Keep all adaptation proposals in PROPOSED state; approval/application stays outside admission and requires its existing explicit governance path.
8. If downstream external side effects are ever required, emit an outbox row in the same transaction and dispatch only after commit.

## Required tests
- Existing trusted learning service tests stay passing.
- First successful capture persists one admission + one memory record + one proposal only for poor outcomes.
- Identical retry returns the same persisted result and does not append records or duplicate classifier-dependent effects.
- Same key / different fingerprint is rejected.
- Inject failure at every persistence stage; all rows roll back.
- Duplicate requests concurrently through independent repository instances: exactly one committed admission.
- Simulate process restart after commit and return the identical result.
- Simulate lost response after commit; retry returns stored result.
- Missing/invalid receipt, gate mismatch, classifier exception, or policy validation failure produces zero writes.
- Migration tests compare JSON source counts, command IDs, stable hashes, and record payloads before enabling the new repository.
- Persistence outage fails closed.

## Migration and rollback gates
1. Back up JSON memory and capture a checksum plus record count.
2. Perform idempotent import into a staging SQLite file; do not delete or overwrite the source JSON.
3. Compare per-record canonical hashes, duplicate command IDs, and total counts.
4. Run failure-injection and recovery tests against the staging copy.
5. Enable the new store only behind an explicit feature flag with documented rollback; preserve the original JSON backup.
6. Require an independent reviewer before marking PR ready or considering merge.

## Release decision
**Production remains HOLD** until service integration, migration proof, independent review, provider authenticity, and target deployment evidence all pass. A green unit-test workflow is not a substitute for these gates.
