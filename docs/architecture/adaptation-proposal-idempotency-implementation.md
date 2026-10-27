# Adaptation Proposal Idempotency — Implementation Notes

## Implemented in this branch

- `SQLiteAdaptationProposalRepository` stores proposals with a unique proposal ID and unique idempotency key.
- Replaying an existing event returns the canonical persisted proposal and current governance status.
- The immutable proposal payload is hashed; reuse of the same event key with different content is rejected.
- Status transitions are persisted and conditional: `PROPOSED → APPROVED/REJECTED`, then `APPROVED → APPLIED`.
- `TrustedDecisionLearningService` accepts an explicit `adaptation_proposal_repository` to enable this durable path.

## Configuration boundary

The repository is opt-in. Callers that do not supply `adaptation_proposal_repository` retain the process-local behavior for backwards compatibility. A production runtime must explicitly configure the durable repository; the presence of this implementation alone does not mean it is active.

SQLite provides durability and uniqueness for processes sharing the same local database file on one host. It is not evidence of safe multi-host coordination or network-filesystem behavior. Multi-host production requires a shared transactional database with an equivalent unique constraint and concurrency validation.

## Verification

The tests added in this branch cover repository recreation, duplicate concurrent callers using independent SQLite connections, conflicting payloads, persisted governance status, and service retry recovery. CI results must be checked for the exact PR head commit before claiming these tests pass.

## Release gate

Keep production on HOLD until the durable repository is configured in the target runtime, shared-storage requirements are satisfied for the deployment topology, CI passes on the reviewed head, independent code review is complete, and authentic provider/outcome plus target-host deployment evidence is verified.
