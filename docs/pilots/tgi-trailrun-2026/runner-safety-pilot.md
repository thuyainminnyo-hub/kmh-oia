# KMH OIA × TGiTrailRun2026 — Runner Safety & Rescue Coordination Pilot

**Status:** DESIGN / IMPLEMENTATION NOT YET VERIFIED  
**Base:** `main` at `032b588cc668c1edc309e8a8276253543427ac76`  
**Branch:** `pilot/tgi-trailrun-runner-safety`  
**Release gate:** HOLD. This pilot is not authorized for live emergency response.

## 1. Objective

Build a small, auditable workflow for checkpoint presence, safety incidents, assignment/acknowledgement, escalation, and post-event review. Integrate with KMH OIA through explicit boundaries; do not bypass its input validation, authorization, trace, or governed-tool execution controls.

This first change defines the contract and verification plan. It does not claim that a live service, medical integration, GPS tracking, SMS delivery, or production database has been implemented.

## 2. Scope

### In scope
- Runner reference IDs and checkpoint arrival/departure events.
- Safety incident creation with severity, reported time, last known checkpoint/location description, status, and assigned response role.
- Append-only audit events for acknowledgement, dispatch, handoff, resolution, and closure.
- Idempotency on client-submitted event IDs; duplicate submissions must not create duplicate incidents or dispatch actions.
- Human-controlled escalation, with visible overdue status and documented fallback contact procedure.
- Synthetic test fixtures and deterministic acceptance tests before any real event data is used.

### Out of scope for the first pilot
- Automated diagnosis, treatment advice, or autonomous medical triage.
- Replacing emergency services, race medical leadership, or the official race command chain.
- Continuous GPS collection, public exposure of runner location, or collection of unnecessary health details.
- Sending real SMS/calls, live dispatch, production deployment, or claiming response-time improvements without measured evidence.

## 3. Architecture mapping

| KMH OIA boundary | Pilot responsibility |
|---|---|
| Input Gateway | Validate event shape, size, IDs, timestamp format, and allowed enum values |
| Context Assembly / Registry | Resolve event, runner pseudonymous ID, checkpoint, and on-duty role references |
| Workflow / Agent | Apply deterministic status-transition rules; AI must not make medical decisions |
| State | Persist incident and idempotency record transactionally in a shared durable store before multi-replica use |
| Tool Security | Authorize role-scoped reads/writes and block unauthenticated public access |
| Governed Tool / Execution Bridge | Create response tasks or notify authorized human responders only after policy checks |
| Evaluation / QA | Verify transitions, audit completeness, duplicates, permissions, failure handling, and recovery |
| Trace | Correlate request, incident, action, result, and evidence IDs without leaking sensitive payloads |

## 4. Data contract

The canonical incident schema is `incident.schema.json` in this directory. All event times must be RFC 3339 timestamps with timezone. IDs are opaque and must not contain names, phone numbers, or other direct identifiers.

Minimum incident fields:
- `schema_version`, `incident_id`, `event_id`
- `event_type`, `severity`, `status`
- `occurred_at`, `recorded_at`
- `checkpoint_id` or a restricted `last_known_location`
- `reported_by_role`, `assigned_to_role`
- `summary_code` (controlled vocabulary; no diagnosis)
- `audit` entries containing actor role, action, timestamp, and result

Keep runner identity data in a separate access-controlled registry. Use a pseudonymous `runner_id` in incident events. Contact details, if operationally necessary, belong in a separate restricted system and must not be copied into logs or test fixtures.

## 5. Workflow and state machine

1. **REPORTED** — authorized reporter submits incident; input validated.
2. **ACKNOWLEDGED** — designated race/medical responder confirms receipt.
3. **DISPATCHED** — authorized coordinator records which response role/team was tasked.
4. **RESOLVED** — qualified responder records the operational outcome; no automated medical judgement.
5. **CLOSED** — incident owner verifies required fields and evidence are present.

Allowed transitions are only:
- REPORTED → ACKNOWLEDGED
- ACKNOWLEDGED → DISPATCHED
- DISPATCHED → RESOLVED
- RESOLVED → CLOSED

An incident may remain in its current state while awaiting human action. Invalid transitions must fail closed and leave an audit record of the rejected attempt where safe. Reopening is not part of v1; if required later, define it as an explicit audited transition. A missing acknowledgement or failed notification must trigger the race's agreed manual fallback; the software is not the sole safety channel.

## 6. Acceptance tests

| ID | Scenario | Expected result | Evidence required |
|---|---|---|---|
| RS-001 | Valid synthetic incident | Accepted with generated/canonical IDs and timestamps | Test output + fixture |
| RS-002 | Missing required field / invalid enum / malformed timestamp | Rejected; no incident or dispatch side effect | Negative test output |
| RS-003 | Duplicate `event_id` submitted twice | One logical event; same result or explicit duplicate response | Persistence assertion |
| RS-004 | Invalid state transition | Rejected; status unchanged | State before/after assertion |
| RS-005 | Unauthorized role attempts read/write | Denied; no sensitive payload disclosed | Authorization test |
| RS-006 | Audit event missing actor/time/action | Rejected; no silent audit gap | Schema/contract test |
| RS-007 | Notification adapter unavailable | Incident remains visible as unacknowledged; fallback is signalled | Fault-injection output |
| RS-008 | Process restart after accepted event | Incident and idempotency key survive restart | Before/after restart receipt |
| RS-009 | Two workers submit same event concurrently | Exactly one logical incident/dispatch action | Concurrent test + DB evidence |
| RS-010 | Sensitive data appears in logs | Test fails; logs use IDs and safe codes only | Captured-log assertion |
| RS-011 | Replay of synthetic audit sequence | Deterministic final state and trace correlation | Replay report |
| RS-012 | Offline/connection-loss simulation | Operator can use documented manual checklist; no false delivery claim | Tabletop checklist signed by owner |

## 7. Verification gates

### Gate A — Contract
- [ ] Schema parses and validates the synthetic fixture.
- [ ] Positive and negative contract tests pass.
- [ ] Existing KMH OIA unit tests remain passing on the exact candidate commit.

### Gate B — State and security
- [ ] Role-based access is tested at the service boundary.
- [ ] Idempotency and state transition are transactionally enforced.
- [ ] Restart persistence is verified against the chosen durable store.
- [ ] Concurrent duplicate submission produces one logical action.
- [ ] Logs and traces contain no direct personal or health data.

### Gate C — Operational rehearsal
- [ ] Race director and medical lead approve role mapping and escalation thresholds.
- [ ] Offline/manual fallback is rehearsed.
- [ ] Notification failures and delayed acknowledgements are rehearsed.
- [ ] No live runner data is used until privacy and access controls are approved.

### Gate D — Promotion
- [ ] Exact-head CI is green.
- [ ] Independent review is complete.
- [ ] Target-host and multi-replica evidence is attached.
- [ ] Medical/event owner signs off.
- [ ] Explicit deployment authorization is recorded.

Until all applicable gates have evidence, status remains **HOLD / NOT VERIFIED**.

## 8. Evidence bundle format

For every run, record:
- Git commit SHA and branch/PR URL.
- Exact command or workflow URL, run ID, timestamp, and outcome.
- Test case IDs and counts (pass/fail/skip).
- Artifact/checksum where available.
- Environment classification: local, CI, staging, or production.
- Explicit gaps: target-host durability, provider delivery, multi-host behavior, and medical/event approval.

CI success is evidence of the tested code path only. It does not prove real-world rescue performance or production readiness.
