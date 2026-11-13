# OIA-CASE-001 — Scope Approval Record

**Purpose:** Record an explicit, scope-specific authorization decision. This template is not an approval and does not authorize execution by itself.

## Current gate

- Status: **HOLD / NOT RUN**
- Runtime execution evidenced: **No**
- Scope approval received: **Pending / not recorded**

## Proposed scope for review

- Input: synthetic/test data only
- Runtime: local runtime only
- Permitted tools: repository checks and local test tools only
- Stop condition: stop immediately and record the event if unexpected output, an error, or an out-of-scope action occurs
- Excluded: production access, external integrations, and sensitive/real data unless separately reviewed and explicitly approved

## Required approval record

- Decision: `PENDING` / `APPROVED` / `REJECTED`
- Approver identity and role: `PENDING — record explicitly; do not infer`
- Approval timestamp (UTC): `PENDING`
- Exact scope approved: `PENDING — quote or attach the approved scope`
- Scope/version or commit reviewed: `PENDING`
- Conditions or limits: `PENDING`
- Evidence/link to approval: `PENDING`

## Pre-run readiness checks

- [ ] Local runtime access and configuration verified
- [ ] Synthetic fixture/input and version identified
- [ ] Output and log locations identified
- [ ] Run ID and timestamp recording method confirmed
- [ ] Stop condition understood
- [ ] QA reviewer identified
- [ ] Scope-specific approval recorded above

## Execution record

Do not start execution while any required gate is pending or unverified.

- Execution status: `NOT RUN`
- Run ID: `N/A`
- Start/end time: `N/A`
- Output/log references: `N/A`
- QA result: `NOT RUN`
- Deviations/incidents: `NONE RECORDED — NOT RUN`

**Rule:** A repository CI pass is not proof of local runtime execution or scope approval. Keep unknowns marked `PENDING`, `NOT RUN`, or `NOT VERIFIED`; do not convert them to pass without evidence.
