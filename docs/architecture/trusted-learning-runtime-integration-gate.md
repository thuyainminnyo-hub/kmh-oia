# Trusted Learning Runtime Integration Gate

## Status

This document is an acceptance contract, not evidence of a live deployment. The runtime integration and production release remain on HOLD until each required check is demonstrated against the exact release candidate.

## Scope

Compose the existing trusted decision-learning service with explicit durable stores and provider-specific trust components. Do not silently fall back to in-memory memory, process-local proposal state, fake provider adapters, or permissive defaults.

## Required composition

- A file-backed `OperatingMemory` configured explicitly.
- A file-backed `SQLiteAdaptationProposalRepository` configured explicitly.
- A `TrustedDecisionLearningService` configured with an independently verifying `TrustedSourceReceiptVerifier` and a real provider-specific `TrustedOutcomeClassifier`.
- An explicit provider allowlist and policy version.
- A documented single-host storage boundary. SQLite local-file persistence is not a multi-host coordination mechanism.
- A runtime entrypoint/factory that fails closed when required configuration is absent or invalid.

## Acceptance matrix

| ID | Scenario | Required assertion |
| --- | --- | --- |
| RLI-01 | Missing verifier | Learning is rejected; no memory event or proposal is created. |
| RLI-02 | Missing classifier | Learning is rejected; no memory event or proposal is created. |
| RLI-03 | Missing/invalid persistent paths | Composition fails before admitting trusted learning; no silent in-memory fallback. |
| RLI-04 | Unapproved decision or failed QA | Learning is rejected and memory remains unchanged. |
| RLI-05 | Receipt/provider/trace attribution mismatch | Learning is rejected and memory remains unchanged. |
| RLI-06 | Valid, independently verified outcome | One event is persisted and a proposal is created only when policy requires it. |
| RLI-07 | Duplicate request after successful completion | The same event/proposal identity is returned; no duplicate event/proposal is created. |
| RLI-08 | Proposal store fails after memory write | Retry converges without duplicating the memory event and without losing the required proposal. |
| RLI-09 | Process restart after success | Event and proposal status are recoverable from configured durable stores. |
| RLI-10 | Process crash at each persistence boundary | Recovery behavior is deterministic and documented; unresolved split-brain states block release. |
| RLI-11 | Concurrent independent processes | Deduplication guarantees match the actual storage implementation; no unsupported guarantee is claimed. |
| RLI-12 | Real provider verification | Provider authenticity, receipt freshness, execution attribution, and outcome mapping are verified with provider-specific evidence—not test fixtures. |
| RLI-13 | Exact release candidate CI | Required tests and validation workflows pass for the exact head SHA under review. |
| RLI-14 | Deployment smoke/restart test | The deployed entrypoint uses the intended configuration and recovers state after restart. |

## Test boundaries

- Unit tests and deterministic fake adapters validate software behavior only.
- CI success does not prove provider authenticity, deployment wiring, production data correctness, or external business outcomes.
- The JSON-backed `OperatingMemory` protects threads sharing one instance; it is not a cross-process transactional store.
- SQLite proposal persistence is separate from memory persistence. There is no atomic transaction spanning both stores; failure injection and recovery tests must cover this boundary.
- Proposal creation must remain governed. No proposed adaptation is automatically promoted or applied.

## Release decision

Keep Production HOLD until the required runtime composition, acceptance tests, independent review, real-provider verification, and target-environment restart evidence are recorded. Record each evidence artifact, tested commit SHA, environment, timestamp, result, and reviewer.

## Evidence record template

For each acceptance ID, record:

- Tested commit SHA:
- Workflow/test command:
- Environment:
- Evidence link or artifact:
- Result: PASS / FAIL / NOT RUN
- Reviewer:
- Notes / limitations:
