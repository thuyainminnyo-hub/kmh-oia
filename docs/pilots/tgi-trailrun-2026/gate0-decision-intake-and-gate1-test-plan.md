# TGiTrailRun Pilot — Gate 0 decision intake and Gate 1 test plan

**Status:** BLOCKED — owner decisions pending  
**PR:** #137  
**Current reviewed candidate (at document creation):** `4cc4499144d951ae0cf9f5b492d3b1d508db58e0`  
**Release:** HOLD — NOT VERIFIED FOR PRODUCTION  
**Data boundary:** Local pilot and synthetic fixtures only. No real runner, medical, or precise location data.

## Purpose

This document separates confirmed evidence from pending decisions. It does not approve live operations, select a provider, or claim tests have run.

## Gate 0 — decision intake

Complete only from a decision made by an authorized owner. Use `UNDECIDED`, `PENDING`, or `DEFERRED` where appropriate.

| Decision | Current status | Required closure evidence |
|---|---|---|
| Pilot entry point | Local CLI/service; synthetic fixtures only | Owner confirms pilot boundary and operational responsibility |
| Future production entry point / hosting | UNDECIDED | Approved choice, accountable hosting owner, target environment |
| Identity provider and credential validation | UNDECIDED | Provider name, documented validation method, test environment owner |
| Authoritative role/checkpoint source | UNDECIDED | Source of truth and assignment-change authority |
| Event owner / race director | PENDING | Name, role, authority, dated decision record |
| Medical lead | PENDING | Name, role, approval of medical boundaries |
| Independent security/privacy reviewer | PENDING | Reviewer and agreed review scope |
| Manual/offline fallback owner | PENDING | Named owner, procedure, acknowledgement expectations |
| Incident severity and escalation | PENDING | Approved severity definitions, escalation path, acknowledgement targets |
| Data retention and audit access | PENDING | Approved retention period, access roles, deletion/review owner |
| Release authority | PENDING | Named release approver and target-host verification criteria |

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

## Gate 2+ dependencies

- Denied/invalid operations have no unauthorized side effects.
- Persistence/restart/concurrency guarantees are demonstrated for the intended target.
- Notifications distinguish recorded, attempted, delivered, and acknowledged.
- Manual/offline emergency procedure is approved and rehearsed.
- Independent security/privacy review and event/medical owner approvals are recorded.

## Current evidence and stop rule

- Previous PR comments record CI and local synthetic verification for candidate `4cc4499144d951ae0cf9f5b492d3b1d508db58e0`; these do not prove production readiness.
- Reviewer status was `COMMENTED`, not approval.
- Gate 1 provider integration tests are NOT RUN.
- Gate 0 remains blocked until authorized decisions and the reviewed data-flow/threat model are recorded.
- Do not implement a live adapter, merge, or deploy while these entry criteria are unmet.
- This pilot must never be the sole emergency-response channel.
