# KMH MediCore — Event Contract v0.1 (Design Draft)

**Product:** KMH MediCore — Powered by KMH OIA  
**Status:** Design draft; not implemented or runtime-verified  
**Scope:** Local pilot using synthetic fixtures only  
**Reference boundary:** Medaius Beta v5 is a functional reference only. This design is original and does not imply Medaius API compatibility.

## 1. Design goals

- Give every requested operation a stable correlation ID and explicit outcome.
- Separate request validation, authorization, execution, audit persistence, and QA.
- Minimize sensitive data in events; never place patient names, patient IDs, clinical notes, tokens, or full records in generic audit payloads.
- Fail closed when authorization or required audit persistence fails.
- Support safe retry through an idempotency key for operations that may cause side effects.
- Keep external delivery disabled until endpoint, authentication, scopes, sandbox, permissions, data-processing terms, and operational limits are verified.

## 2. Event envelope

Proposed JSON shape (illustrative, not yet a runtime schema):

```json
{
  "event_id": "evt_<unique-id>",
  "event_type": "request.received",
  "event_version": "0.1",
  "occurred_at": "2026-01-01T00:00:00Z",
  "correlation_id": "req_<safe-id>",
  "producer": "kmh-medicore-local-pilot",
  "environment": "local-synthetic",
  "data_classification": "synthetic",
  "outcome": "accepted",
  "payload": {}
}
```

Rules:
- Timestamps are UTC ISO-8601.
- IDs are opaque, bounded, and validated; do not encode personal information in them.
- `payload` is event-specific and allow-listed. No arbitrary record dumps.
- Unknown event versions are rejected or quarantined; never silently interpreted.
- The example timestamp and IDs are illustrative only.

## 3. Initial event types

| Event type | Required safe fields | Meaning |
|---|---|---|
| `request.received` | correlation ID, operation name | Request entered the local boundary |
| `request.validated` | validation policy version, outcome | Input contract checked |
| `access.checked` | policy ID/version, decision | Authorization decision recorded without secrets |
| `execution.started` | operation name, idempotency key hash/reference | Authorized operation began |
| `execution.completed` | outcome, result reference | Operation completed; avoid embedding records |
| `execution.failed` | stable error code, retryable flag | Operation failed safely |
| `audit.persisted` | audit reference, persistence outcome | Required audit record was persisted |
| `qa.completed` | check suite version, pass/fail, evidence reference | Result compared against acceptance criteria |
| `decision.recorded` | promote/hold/rollback, approver reference | Release or workflow decision recorded |

## 4. Required control flow

1. Parse and validate the request.
2. Establish a non-sensitive correlation ID.
3. Check authorization and policy.
4. Persist the required audit decision before any protected side effect.
5. Execute only within the explicitly allowed local pilot boundary.
6. Persist a minimal result event.
7. Run QA/reconciliation checks.
8. Hold the result if required audit, authorization, or QA gates fail.
9. Record the final decision and evidence references.

## 5. Retry and idempotency

- Use a caller-supplied or generated idempotency key for side-effecting operations.
- Store only a safe hash/reference of the key in general audit events.
- Repeated requests with the same key and same request fingerprint should return the recorded outcome rather than repeat the side effect.
- Reuse of a key with a different request fingerprint must be rejected.
- Retry only transient failures; use bounded attempts and backoff.
- Do not retry authorization denials, invalid payloads, or policy failures automatically.

## 6. Acceptance tests required before calling this implemented

- Valid synthetic request produces a traceable event sequence.
- Invalid schema is rejected before execution.
- Denied authorization prevents execution.
- Required audit persistence failure prevents protected output/action.
- Duplicate delivery does not duplicate a side effect.
- Reusing an idempotency key with different request content is rejected.
- Audit events contain no patient identifier, patient name, clinical note, token, or full clinical record.
- Unknown event version fails safely.
- QA failure records a hold decision and prevents promotion.
- Fixture provenance is controlled separately; a `synthetic: true` marker alone is not proof of synthetic provenance.

## 7. Explicit non-goals / release gates

This draft does not implement a webhook server, DHIS2 connector, ICD-10/LOINC terminology service, clinical decision support, production database, or external API calls. It does not establish regulatory compliance or clinical safety. Any real-patient-data use, external integration, merge, or deployment requires separate authorization, security/privacy review, authoritative integration documentation, and test evidence.

## 8. Status tracking

- [x] Draft event vocabulary and envelope proposed.
- [ ] Convert the envelope into a machine-validated schema.
- [ ] Implement local event validation and tests.
- [ ] Implement append-only audit persistence and failure tests.
- [ ] Implement idempotency/retry behavior for a bounded local test operation.
- [ ] Run CI against the exact candidate commit.
- [ ] Obtain independent review.
