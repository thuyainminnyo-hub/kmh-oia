# TGiTrailRun Pilot — Manual/Offline Fallback Template

**Status:** TEMPLATE ONLY — NOT REVIEWED OR APPROVED FOR LIVE EVENT USE  
**Effective date:** 2026-10-28  
**Permitted scope:** Local CLI/service with synthetic fixtures only  
**Release status:** HOLD — NOT VERIFIED FOR PRODUCTION

## 1. Purpose and boundary

This document is a controlled fallback template for local synthetic verification of the TGiTrailRun runner-safety pilot. It is not an event operations plan, medical protocol, emergency-response procedure, or approval to use the pilot with real runners.

- Use synthetic fixtures only. Do not enter real runner identities, medical details, contact details, or precise location data.
- Do not connect live identity, messaging, checkpoint, tracking, or notification providers under this template.
- Do not treat a log entry, locally recorded notification, or successful test as proof that a person was contacted or that an incident has been handled.
- The pilot must never be the sole emergency-response channel.

## 2. Stop conditions

Stop the current synthetic test and preserve its evidence if any of the following occurs:

- Authentication, identity, role, or checkpoint scope is missing, invalid, or uncertain.
- A dependency is unavailable or its result cannot be verified.
- A denied action appears to change state or create a receipt.
- State, receipt, audit, or notification status is inconsistent with the expected result.
- A test produces unexpected side effects, duplicate records, or unclassified errors.
- The operator cannot establish which commit, fixture, or command produced the result.

**Fail closed:** do not bypass identity/scope checks, edit persistent state manually to force a pass, or relabel an unknown outcome as success.

## 3. Local synthetic fallback procedure

1. **Stop:** cease the current test. Do not continue an ambiguous or potentially inconsistent run.
2. **Isolate:** confirm that the test uses only synthetic data and local resources. If that cannot be confirmed, stop and escalate to the accountable project owner without copying sensitive data into the record.
3. **Record:** capture the test ID, UTC timestamp, commit SHA, command, fixture identifier, expected outcome, observed outcome, exit status, and relevant redacted log/artifact references.
4. **Protect evidence:** keep the original failure evidence. Do not overwrite it with a later retry or modify records to make the test appear successful. Never include tokens, credentials, or personal data.
5. **Recover only within the test boundary:** use a documented, reviewed synthetic-fixture reset procedure if one exists. If no such procedure exists, do not improvise a reset; mark the test BLOCKED and request an implementation/review decision.
6. **Re-run deliberately:** only after the cause is understood and the synthetic test state is known. Record the retry as a new attempt linked to the original failure.
7. **Verify:** compare state, receipts, audit events, and expected side effects. Re-run the applicable QA checks. A retry does not erase the original failure.
8. **Close or hold:** mark PASS only when the required evidence exists and matches the exact commit. Otherwise mark FAIL or BLOCKED and keep the release HOLD.

## 4. Real-event and offline-use restriction

This pilot is not approved for real-event operation and must not replace an organizer-approved emergency plan. If a real-world emergency occurs, follow the event's established emergency procedures and contact local emergency services as appropriate; do not depend on this pilot or its logs for emergency response.

Any future real-event use requires, at minimum, a selected and reviewed hosting/identity design, independently reviewed security and privacy controls, verified target-environment tests, an approved and rehearsed event-specific fallback plan, event-owner/race-director authorization, qualified medical-lead approval, and explicit release authorization. This template satisfies none of those approvals by itself.

## 5. Review and approval register

All entries begin **PENDING**. The pilot owner cannot self-certify independent review.

| Required record | Status | Evidence to attach |
|---|---|---|
| Independent security review | PENDING | Reviewer identity, review date, findings, disposition |
| Independent privacy review | PENDING | Data inventory, retention/deletion review, access-control findings, reviewer sign-off |
| Synthetic fallback rehearsal | NOT RUN | Exact commit, fixture, command, observations, artifact, reviewer |
| Event-owner/race-director approval for real use | NOT APPROVED | Explicit authority confirmation for the named event |
| Qualified medical-lead approval for real use | NOT APPROVED | Qualified person's approval and scope |
| Release authorization | HOLD | Closure evidence for all applicable gates |

## 6. Execution record template

Copy this block for each local synthetic exercise:

```text
Status: NOT RUN
Test ID:
Attempt:
Date/time (UTC):
Commit SHA:
Command:
Synthetic fixture ID:
Expected result:
Observed result:
State/receipt/audit comparison:
Artifact or redacted log reference:
Failure classification / root cause:
Recovery performed (if any):
QA result:
Operator:
Independent reviewer:
Open issues:
```

Allowed result states are **NOT RUN**, **PASS**, **FAIL**, and **BLOCKED**. Do not use PASS without repeatable evidence tied to the exact commit and fixture.

## 7. Exit criteria

This template may be considered reviewed for local synthetic use only after the fallback procedure and reset assumptions are independently reviewed, the synthetic exercise is executed and recorded, and all findings are dispositioned. Real-event use remains prohibited until the separate operational, security, privacy, event-owner, medical, and release gates have been explicitly satisfied.

**Current decision: DESIGN-ONLY SYNTHETIC STAGING. Production remains HOLD — NOT VERIFIED FOR PRODUCTION.**
