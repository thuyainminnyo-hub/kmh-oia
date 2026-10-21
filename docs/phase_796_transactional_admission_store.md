# Phase 796–798 — Transactional Learning Admission

## Implementation history
- **Phase 796:** Added `src/learning_admission_repository.py`, a local SQLite transaction boundary for an admission result, learning record, optional PROPOSED adaptation proposal, and audit event.
- **Phase 797–798:** Integrated `TrustedDecisionLearningService` with the repository; the service now requires an explicit repository dependency and no longer writes admitted records through `OperatingMemory.record()`.
- **Current behavior:** stable admission key derived from decision/execution/evidence identity; canonical SHA-256 fingerprint over verified request facts and policy context; same-identity/same-fingerprint retries return the persisted result before reclassification; changed content under the same identity is rejected; proposal IDs tie back to the admission key.

## Test coverage
- Repository-level tests cover transaction rollback injection, durable restart readback, same-key retry, fingerprint conflict, concurrent duplicate requests, and the PROPOSED-only governance boundary.
- Service-level tests cover trust-chain rejection, verified admission persistence, duplicate retry without reclassification, and policy fingerprint conflict.
- Governed-orchestrator tests construct the service with a temporary SQLite repository and verify successful admissions are written there rather than to the legacy JSON memory store.

## Exact-head evidence for the code integration
On code/test head `fb2bbd5f834a90f415c7f59c4311fa719dd1b77d`:
- [KMH OIA Tests #754 — SUCCESS](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/39599257017), with the test log reporting 529 tests run.
- [KMH OIA Validation #673 — SUCCESS](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/39599257142); tests, repository-validation, performance-evidence, and deployment-evidence-bundle all passed.

The workflows shown above verify the integration code/test head. Every subsequent source or documentation commit remains subject to the PR's required current-head CI checks before merge.

## Remaining constraints
- Fingerprinting identifies the classifier by type and optional version string, not by an immutable content-addressed artifact digest. Production should pin and record the exact classifier/policy artifact version.
- SQLite is local-filesystem persistence. Shared multi-host semantics are not established.
- JSON-to-SQLite migration still requires source backup, record-count/hash reconciliation, staging validation, and a rollback drill.
- Real external provider authenticity, target-runtime wiring/deployment evidence, live external outcome verification, independent review, and release sign-off remain outstanding.
- Proposals remain `PROPOSED`; approval/application are separate governed actions.

## Release decision
**Production remains HOLD.** Green CI is repository/test evidence, not production deployment proof or independent human approval.
