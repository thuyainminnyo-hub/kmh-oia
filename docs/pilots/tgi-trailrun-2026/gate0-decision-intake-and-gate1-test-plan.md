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
- Gate 0 is partially documented for design-only synthetic staging; independent review and supporting evidence remain open.
- Keep any Gate 1 work restricted to local synthetic staging. Do not implement live integrations, merge for production, or deploy while these entry criteria are unmet.
- This pilot must never be the sole emergency-response channel.
