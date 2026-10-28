# TGiTrailRun Pilot — Reviewer Remediation and Release Gates

**Status:** OPEN — planning and acceptance criteria only  
**Current PR:** #137  
**Current PR head:** `332f494c843af3170a13a00c3ee7547dd00adc76`  
**Release decision:** HOLD — NOT VERIFIED FOR PRODUCTION  
**Data policy:** Synthetic fixtures only. Do not use real runner, medical, or location data.

This plan translates the review from `zinbo2024-bit` into ordered, evidence-based gates. It does not select an identity provider or framework on behalf of the event owner, and it does not authorize live operations.

## Gate 0 — Confirm operational requirements before implementation

**Owner decision required before writing a live adapter:**
- [ ] Select the supported entry point and hosting model (for example, a documented API or operator application).
- [ ] Select the identity provider and approved authentication/session/token validation method.
- [ ] Name the authoritative source for user-to-role assignment and checkpoint entitlements.
- [ ] Identify the event owner/race director, medical lead, security/privacy reviewer, and operational fallback owner.
- [ ] Define the event's approved incident severity, escalation, retention, and audit-access policies.

**Acceptance evidence:** recorded decisions, named accountable owners, and an approved data-flow/threat model. Do not infer these choices from the current CLI or from caller-supplied role strings.

## Gate 1 — Trusted identity and resource scope

Implement only after Gate 0 decisions are recorded.
- [ ] The entry point validates identity using the selected provider's documented verification mechanism.
- [ ] Role and allowed checkpoint scope are derived server-side from authoritative assignments, never trusted from request JSON or unverified headers.
- [ ] The adapter fails closed for missing, invalid, expired, or ambiguous identity and missing/unknown checkpoint entitlement.
- [ ] Tests demonstrate that a caller cannot elevate role or change checkpoint scope by editing request fields.
- [ ] Audit events record a stable, privacy-reviewed actor subject identifier from verified identity; avoid unnecessary personal data.

**Acceptance evidence:** integration tests against the selected adapter/provider test setup, including forged-role, forged-scope, expired-credential, and unknown-identity cases.

## Gate 2 — No side effects on denied or invalid requests

- [ ] Denied create/read/audit/transition requests do not mutate incident rows, event receipts, status, or audit records.
- [ ] Schema-invalid payloads and role/reporter mismatches are rejected before persistence.
- [ ] Retries after denied create attempts behave as new valid requests when subsequently authorized; they must not be blocked by ghost receipts.
- [ ] Error responses and logs do not expose secrets, credentials, raw health details, or unnecessary location/personal data.

**Acceptance evidence:** integration tests assert database state and authoritative audit/receipt counts before and after each denied request.

## Gate 3 — Persistence, restart, and concurrency

- [ ] Select and document the intended persistence adapter and its operational guarantees.
- [ ] Restart/recovery tests prove incident status, authoritative audit history, and idempotency receipts remain consistent.
- [ ] Multi-worker concurrency tests prove that duplicate event delivery cannot create duplicate incidents or divergent audit histories.
- [ ] Corruption, partial failure, and storage unavailability fail closed with actionable, privacy-safe diagnostics.
- [ ] Backup, restore, retention, access control, and recovery objectives are documented and exercised for the target environment.

**Acceptance evidence:** repeatable integration-test logs and a reviewed persistence/recovery runbook. The current local SQLite adapter alone does not establish multi-host production guarantees.

## Gate 4 — Notification and offline failure handling

- [ ] Select notification channels and define delivery, retry, timeout, duplicate suppression, and failure visibility.
- [ ] Tests cover provider timeout, rejection, rate limiting, duplicate delivery, and total outage.
- [ ] Define and rehearse an offline/manual escalation procedure with named roles and acknowledgement expectations.
- [ ] The application clearly distinguishes incident recorded, notification attempted, notification delivered, and responder acknowledgement.
- [ ] No automated status may imply that rescue has been dispatched or completed without authoritative evidence.

**Acceptance evidence:** integration-test results and event-owner-approved fallback procedure. This pilot must never be the sole emergency-response channel.

## Gate 5 — Independent review and controlled release decision

- [ ] Independent security/privacy review closes the relevant findings.
- [ ] Race director/event owner approves the operating procedure and escalation responsibilities.
- [ ] Medical lead approves medical-related boundaries and confirms the software does not replace clinical judgement.
- [ ] Target-host configuration, access controls, monitoring, backups, incident response, and rollback are verified.
- [ ] Exact release SHA, test evidence, open risks, and approvals are recorded.
- [ ] Any live rehearsal is separately authorized and uses a reviewed safety plan; no real data is used in ordinary synthetic CI.

**Acceptance evidence:** dated approvals and target-environment verification tied to the exact candidate SHA.

## Current evidence snapshot

- PR #137 is Open / Draft / not merged; `zinbo2024-bit` remains requested as reviewer.
- Current PR head is `332f494c843af3170a13a00c3ee7547dd00adc76`.
- [KMH OIA Tests #40725543843](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40725543843) passed on this exact head: `Ran 517 tests in 0.974s`, `OK`.
- [KMH OIA Validation #40725543953](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40725543953) passed on this exact head; tests, repository validation, performance evidence, and deployment evidence bundle succeeded.
- A local Colab run was reported for earlier commit `4cc4499144d951ae0cf9f5b492d3b1d508db58e0` (Python 3.12.3, 514 tests, `OVERALL_RESULT=PASS`). Because it was not executed at this current head, it is historical supporting evidence, not an exact-head local verification record for `332f494...`.
- The reviewer provided a COMMENTED review, not production approval.
- Authentication adapter, trusted role/checkpoint derivation, stable verified actor-subject audit attribution, target-host verification, and event/medical-owner approvals remain open.

## Stop rule

Keep **HOLD — NOT VERIFIED FOR PRODUCTION** until the relevant gates have explicit evidence and named-owner approval. Do not merge or deploy as part of this plan. Never use this pilot as the sole emergency-response channel.
