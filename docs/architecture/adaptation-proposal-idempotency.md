# Adaptation Proposal Idempotency — Design and Acceptance Criteria

## Status

Design proposal only. This document does not claim that durable proposal persistence has been implemented. The current PR #123 head has green CI, but `AdaptationEngine.propose()` currently returns an in-memory `AdaptationProposal`; it does not persist proposals or recover an existing proposal by ID.

## Problem statement

The trusted learning service deduplicates an `OperatingMemoryRecord` using a stable `event_id`. For a POOR outcome, each retry still calls `AdaptationEngine.propose()`. The proposal ID can be deterministic, but a deterministic ID alone does not guarantee one durable proposal, preserve the original status, or recover after a process restart.

## Required behavior

For a given trusted learning event, proposal creation must be idempotent across retries and process restarts. Existing proposal status must not be reset by replaying the same event. Conflicting content for the same identity must be rejected or handled by an explicit immutable-event policy.

## Proposed design

1. **Proposal repository contract**
   - Add a repository abstraction with an idempotent `get_or_create(proposal, idempotency_key)` operation.
   - The key should be the stable learning `event_id`, or a documented stable proposal ID derived from it.
   - Return the persisted canonical proposal, including its current status, whether it was newly inserted or already existed.

2. **Durable uniqueness**
   - Enforce a unique constraint on the idempotency key in the durable storage layer.
   - Do not rely on an in-process lock, pre-insert read, or deterministic ID alone for cross-process safety.
   - Use a transactional shared database for multi-process or multi-host deployment. A local-only adapter may be used for tests or single-process development, but its limits must be explicit.

3. **Immutable identity and conflict handling**
   - Store a canonical payload or payload hash alongside the key.
   - If the same key is submitted with materially different proposal content, reject it with a clear conflict rather than silently overwriting the original.
   - Replaying an event must preserve an existing `PROPOSED`, `APPROVED`, `REJECTED`, or `APPLIED` status; replay must not reset governance state.

4. **Service integration**
   - Route POOR-outcome proposal creation through the repository.
   - Keep proposal creation separate from automatic application. A proposal must remain `PROPOSED` until the existing governance approval path changes its status.
   - Define the failure boundary if memory-event persistence succeeds but proposal persistence fails. Retrying the same event must complete or recover the proposal without duplicating the memory event.

5. **Operational evidence**
   - Expose repository-level results sufficient to audit whether a proposal was created or reused.
   - Do not interpret a content hash or idempotency key as proof that provider evidence is authentic; receipt verification remains a separate gate.

## Acceptance criteria

- [ ] Repeating the same trusted event returns the same durable proposal ID and canonical persisted record.
- [ ] Repeating the same event after repository/process restart returns the existing proposal.
- [ ] Two concurrent workers submitting the same key create exactly one durable row/record.
- [ ] A simulated failure after durable proposal insertion but before response delivery is recovered by retry without a duplicate.
- [ ] A memory write followed by proposal-store failure can be retried successfully; the memory event remains deduplicated.
- [ ] Replaying an event does not reset a proposal's governance status.
- [ ] Same key with conflicting proposal payload is rejected or follows a documented deterministic conflict policy.
- [ ] Tests use the actual persistence implementation, not only a mocked or in-memory engine.
- [ ] Storage-specific tests verify uniqueness and transaction behavior; cross-host guarantees are not inferred from unit tests.
- [ ] Existing trusted receipt, attribution, QA, and evidence-admission fail-closed tests continue to pass.

## Suggested implementation sequence

1. Identify the project's supported durable storage and migration conventions.
2. Implement repository interface and storage-backed unique-key constraint.
3. Add service-level get-or-create integration for adaptation proposals.
4. Add restart, concurrent retry, conflict, and partial-failure tests.
5. Run the complete CI and review the storage/deployment configuration.
6. Obtain independent review before changing the PR from draft or considering release.

## Release gate

This design does not authorize merge or production release. Keep production on HOLD until shared transactional storage, authentic provider evidence, external outcome evidence, target-host deployment verification, and independent governance review are separately evidenced.
