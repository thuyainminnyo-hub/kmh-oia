# TGiTrailRun Pilot — Gate 0 decision intake and Gate 1 test plan

**Status:** PARTIALLY DOCUMENTED — design-only synthetic staging; independent review and evidence gaps remain  
**PR:** #137  
**Current reviewed candidate (at document creation):** `4cc4499144d951ae0cf9f5b492d3b1d508db58e0`  
**Release:** HOLD — NOT VERIFIED FOR PRODUCTION  
**Data boundary:** Local pilot and synthetic fixtures only. No real runner, medical, or precise location data.

## Purpose

This document separates confirmed evidence from pending decisions. It does not approve live operations, select a provider, or claim tests have run.

## Gate 0 — decision intake

Owner response recorded on 2026-10-28 by `thuyainminnyo-hub` (Solo Architect & Lead Developer). Scope approved for design work only in a local CLI/service with synthetic fixtures. This is not production approval. Values below are recorded proposals/decisions and must not be treated as independently verified controls.

| Decision | Current status | Required closure evidence |
|---|---|---|
| Pilot entry point | **Confirmed for design-only staging:** local CLI/service; synthetic fixtures only | Recorded owner response dated 2026-10-28; live operation remains out of scope |
| Future production entry point / hosting | UNDECIDED | Approved choice, accountable hosting owner, target environment |
| Identity provider and credential validation | **Proposed staging stub:** internal JWT / local token authentication; local cryptographic bearer-token validation; environment owner `thuyainminnyo-hub` | Link the referenced staging specs; verify signature/issuer/audience/expiry/revocation behavior and fail-closed handling; production provider remains undecided |
| Authoritative role/checkpoint source | **Local staging proposal:** SQLite role/checkpoint tables; changes via Solo Developer/Admin CLI; local audit logs | Review authorization bypass risks, migration/change controls, and audit integrity; this is not a production authoritative source |
| Event owner / race director | `thuyainminnyo-hub` self-assigned for local pilot | For real event operations, obtain event-owner/race-director authority confirmation |
| Medical lead | `thuyainminnyo-hub` self-assigned as staging safety lead | Independent qualified medical lead approval is still required before operational use |
| Independent security/privacy reviewer | **PENDING** — owner proposed self-attestation | Self-attestation does not satisfy independent review; appoint a separate reviewer |
| Manual/offline fallback owner | `thuyainminnyo-hub` for local pilot | Provide a reviewable runbook and verify the fallback procedure; not a live-event fallback approval |
| Incident severity and escalation | Local INFO/ERROR/FATAL logs and local notification proposed | Logs/local feedback do not define operational severity, escalation ownership, acknowledgement SLA, or emergency fallback; owner approval and runbook evidence remain open |
| Data retention and audit access | Synthetic/mock payloads only; transient local storage/manual purge; Admin/Solo Developer access | Link privacy review and runbook; validate deletion, access control, and audit retention behavior |
| Release authority | **HOLD** — no production release authorized | Independent security/privacy review, qualified event/medical approvals, target-host evidence, and explicit release authorization |

### Owner decision record template

```text
Decision date:
Event/pilot:
Decision owner, role, and authority:

Pilot boundary:
Future hosting/entry point:
Identity provider and validation method:
Authoritative role/checkpoint source:
Who can change assignments:
Event owner/race director:
Medical lead:
Independent security/privacy reviewer:
Manual/offline fallback owner:
Severity and escalation policy:
Retention and audit-access policy:
Decision: APPROVE DESIGN / DEFER / REJECT LIVE OPERATION
Conditions and unresolved risks:
Evidence/meeting-record link:
```

Do not paste tokens, credentials, real runner records, medical details, or precise location data into the issue.


## Owner response recorded — 2026-10-28

The owner approved **design work only**, limited to local staging and synthetic fixtures. The stated CI successes for PR #137/#139 are engineering evidence, not identity-provider approval or operational readiness. The following are proposals for a local stub, not a verified production security boundary:

- Internal JWT/local token authentication with local cryptographic bearer-token validation.
- SQLite role/checkpoint tables and Admin CLI assignment changes with local audit logs.
- Local INFO/ERROR/FATAL logging and local execution feedback.
- Synthetic/mock data only, transient local storage, manual purge, Admin/Solo Developer audit access.

**Remaining Gate 0 conditions:** independently appointed security/privacy reviewer; reviewable links for the staging architecture spec, local runbook, and privacy self-review; clear incident severity/escalation and offline fallback procedures; confirmation of any event/medical authority before any real event use. Self-attestation is not independent review.

## Gate 1 — test contract (design only; NOT RUN)

| ID | Scenario | Expected result | Required evidence |
|---|---|---|---|
| G1-01 | Missing, invalid, expired, revoked, or unknown identity | Protected request denied; no state mutation | Provider integration test after provider selection |
| G1-02 | Forged role in request JSON or unverified header | No privilege elevation | Authorization integration test |
| G1-03 | Forged or unauthorized checkpoint scope | Access denied; incident state/receipts/audit counts unchanged | Scope enforcement test |
| G1-04 | Identity/entitlement source unavailable | Fail closed for protected operations | Failure-injection test |
| G1-05 | Caller-supplied actor label | Not used as trusted audit identity | Audit attribution test |
| G1-06 | Denied create followed by authorized retry | No ghost receipt blocks valid retry | Persistence/receipt integration test |

For every test, record `NOT RUN`, `PASS`, or `FAIL`; exact commit SHA; command; environment; artifact; reviewer. A written test contract is not a test result.

## Reviewer feedback from PR #137 — blockers, not approval

The PR #137 reviewer noted that this change is a contract/specification slice, not a live runner-safety service. The synthetic fixture and identity-boundary contract are useful safeguards, but authentication, server-derived role/checkpoint scope, durable adapter behavior, notification delivery, runtime persistence, and owner approvals are not implemented or verified. The reviewer explicitly said this comment is **not production approval** and that Production HOLD must remain.

Convert that feedback into the following evidence requirements. These are planned tests only; none should be marked PASS without a run record tied to the exact candidate commit.

## Gate 2+ test contract (design only; NOT RUN)

| ID | Scenario | Expected result | Required evidence |
|---|---|---|---|
| G2-01 | Restart process/service after a synthetic incident is recorded | Required incident state and receipt survive according to the chosen persistence contract; no partial record | Exact commit, restart integration test, state/receipt comparison |
| G2-02 | Retry the same synthetic request concurrently across workers | One idempotent outcome; no duplicate receipt or inconsistent state; storage claim is atomic for the intended deployment model | Multi-worker concurrency test against the intended transactional store; repeatable artifact |
| G2-03 | Attempt to spoof actor, role, or checkpoint attribution | Audit uses authenticated subject and server-mapped role/scope; denied attempts do not alter incident/receipt state | Identity-boundary integration test and inspected audit entries |
| G2-04 | Notification is recorded, attempted, delivered, acknowledged, delayed, or fails | Statuses are not conflated; failed delivery/acknowledgement is observable and follows the approved escalation policy | Fault-injection test plus delivery/acknowledgement evidence |
| G2-05 | Identity source, storage, network, or notification dependency becomes unavailable | Protected actions fail closed; no unauthorized/partial mutation; manual/offline procedure is explicit | Failure-injection evidence and reviewed runbook |
| G2-06 | Manual/offline fallback exercise using synthetic fixture | Named operator can follow the approved local procedure and record its result without relying on this pilot as the sole emergency channel | Rehearsal record, reviewer, unresolved failure list |

The selected real entry point/provider and intended runtime/storage model must be decided before any provider-specific or production-target integration test can be meaningful. Do not substitute a fake verifier or mock-only test for verification at the actual authentication boundary.

- Denied/invalid operations have no unauthorized side effects.
- Persistence/restart/concurrency guarantees are demonstrated for the intended target.
- Idempotency is tested under multi-worker concurrency where the intended deployment can run multiple workers.
- Audit attribution is derived from verified identity and server-side role/scope mapping.
- Notifications distinguish recorded, attempted, delivered, and acknowledged.
- Manual/offline emergency procedure is approved and rehearsed.
- Independent security/privacy review and event/medical owner approvals are recorded.

## Evidence inventory — inspected artifacts and limitations

The following repository artifacts were inspected on 2026-10-28. These are links to existing design/review materials, not substitutes for an independent approval or runtime evidence:

- [Trusted Identity Adapter Contract](https://github.com/thuyainminnyo-hub/kmh-oia/blob/pilot/tgi-trailrun-runner-safety/docs/pilots/tgi-trailrun-2026/identity-adapter-contract.md) — design contract only; provider/framework not selected and authentication is not implemented.
- [Security Review Note](https://github.com/thuyainminnyo-hub/kmh-oia/blob/pilot/tgi-trailrun-runner-safety/docs/pilots/tgi-trailrun-2026/security-review-note.md) — records open security gaps and explicitly retains HOLD; not an independent security/privacy certification.
- [Reviewer Remediation and Release Gates](https://github.com/thuyainminnyo-hub/kmh-oia/blob/pilot/tgi-trailrun-runner-safety/docs/pilots/tgi-trailrun-2026/reviewer-remediation-and-release-gates.md) — defines acceptance gates, but the listed criteria are not evidence that they have passed.
- [Local Synthetic Verification Matrix](https://github.com/thuyainminnyo-hub/kmh-oia/blob/pilot/tgi-trailrun-runner-safety/docs/pilots/tgi-trailrun-2026/local-verification-matrix.md) — explicitly says local execution results have not been recorded; authentication and trusted checkpoint assignment remain blocked by design.
- [Runner Safety Pilot Overview](https://github.com/thuyainminnyo-hub/kmh-oia/blob/pilot/tgi-trailrun-runner-safety/docs/pilots/tgi-trailrun-2026/runner-safety-pilot.md) — documents scope and design boundary; not operational approval.

**Still missing from the inspected pilot evidence set:** a separately approved pilot-specific manual/offline fallback runbook; a documented privacy review performed by an independent reviewer; a selected real entry point/provider; provider integration results; and event-owner/race-director plus qualified medical-lead approval for any real operation. Do not treat the linked design notes as satisfying these items.

## CI evidence separation — 2026-10-28

The workflow logs were inspected and the two pull requests' evidence must be kept separate:

| Candidate / purpose | Exact commit SHA | Verified CI evidence | Scope limitation |
|---|---|---|---|
| PR #137 — TGiTrailRun pilot code | `4cc4499144d951ae0cf9f5b492d3b1d508db58e0` | [Tests run](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40649395767) and [Validation run](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40649395763) both completed successfully; each test job log reports **514 tests, OK** and includes TGiTrailRun-specific tests. | CI evidence for the synthetic pilot code at this exact candidate only. It does not prove trusted authentication, live notification delivery, real event readiness, or production safety. |
| PR #139 — documentation-only branch | `9d5db58be622e060d8cd963f66d5d0a03fbc7d68` | [Tests run](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40685670192) and [Validation run](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40685669938) both completed successfully; test logs report **462 tests, OK**. | This branch is based on `main` and its test log contains no TGiTrailRun-specific test names. Do not use these runs as proof that the separate PR #137 code was tested. |

The shell-based local verification procedure was **not run in a local workstation/Codespace in this session** because the runtime could not resolve `github.com` for a repository clone. Do not label the CI executions as local verification. The repository's `local-verification-matrix.md` remains a pending execution-record template, not a completed local run.

## Current evidence and stop rule

- Previous PR comments record CI and local synthetic verification for candidate `4cc4499144d951ae0cf9f5b492d3b1d508db58e0`; these do not prove production readiness.
- Reviewer status was `COMMENTED`, not approval.
- Gate 1 provider integration tests are NOT RUN.
- Gate 0 is partially documented for design-only synthetic staging; independent review and supporting evidence remain open.
- Keep any Gate 1 work restricted to local synthetic staging. Do not implement live integrations, merge for production, or deploy while these entry criteria are unmet.
- This pilot must never be the sole emergency-response channel.
