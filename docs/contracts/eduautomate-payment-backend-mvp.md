# EduAutomate Payment Backend MVP — Phase 821 Contract Proposal

Status: DESIGN PROPOSAL ONLY — NOT IMPLEMENTED; NOT PRODUCTION EVIDENCE

## Purpose and boundary

Build the smallest EduAutomate backend slice that can persist and retrieve payment records, document its API, and later provide a source record to KMH OIA's existing `TrustedSourceReceiptVerifier`.

This document is a contract proposal, not a claim that the backend, database, payment provider integration, or production evidence exists. Do not create a provider-specific OIA adapter until the selected payment provider and its documented verification mechanism are known.

A record written by EduAutomate alone proves what EduAutomate stored; it does not independently prove that funds settled. For externally verified payment outcomes, retain the payment provider's stable transaction ID and verify the provider's signed webhook or authenticated provider-side transaction lookup. If payments are recorded manually, label that evidence as internally attested, not provider-authenticated.

## Proposed first vertical slice

- Create a payment record with status `pending`.
- Retrieve a record by its stable internal ID.
- Change a payment to `confirmed` only from an authenticated, authorized and auditable confirmation path.
- Preserve provider transaction identity and the KMH OIA `execution_id` correlation when an execution is genuinely related to the payment.
- Keep raw provider observation separate from normalized business interpretation.
- Do not store card numbers, CVV, bank passwords, payment credentials or provider secrets.

## Minimal API contract (version 1)

Base path: `/v1`

### `POST /v1/payments`

Create a pending payment record. Requires authenticated staff/service identity and an idempotency key.

Request:
```json
{
  "student_id": "stu_01J...",
  "amount_minor": 18000000,
  "currency": "MMK",
  "purpose": "course_fee",
  "execution_id": "oia_exec_...",
  "idempotency_key": "client-generated-unique-value"
}
```

Contract notes:
- `amount_minor` is a positive integer in the currency's minor-unit convention; define and test the MMK amount convention before implementation. Never use floating-point money.
- `student_id` is an internal opaque identifier; do not put student names or other unnecessary personal data into OIA evidence.
- `execution_id` is optional unless the business flow explicitly has an OIA execution to correlate. It must never be fabricated to make evidence pass.
- A repeated idempotency key with the same request returns the original result; the same key with a different payload returns `409 Conflict`.
- Return `201 Created` for a new record and a stable `payment_id`.

### `GET /v1/payments/{payment_id}`

Return the authorized caller's payment record, including current status, timestamps and any provider transaction reference. Apply tenant/ownership authorization; knowing an ID is not authorization.

### Provider confirmation path — not implementable until provider is selected

Preferred option: a provider webhook endpoint such as `POST /v1/payment-provider-events/{provider_name}`, after the exact provider is selected and its official signature-verification and retry documentation are reviewed.

The handler must:
1. verify the provider signature over the original raw request bytes using the provider's documented algorithm and a secret held outside source control;
2. enforce timestamp/replay tolerance and deduplicate stable provider event IDs;
3. verify the transaction with the provider API when supported;
4. confirm that amount, currency, merchant/account and payment reference match the pending payment;
5. commit event receipt and state transition atomically;
6. return a safe error and leave the payment unconfirmed on any verification failure.

Do not expose a generic unauthenticated endpoint that lets a caller mark a payment as paid. Do not invent signature headers or claim authenticity before the provider is selected.

### Suggested response fields

```json
{
  "payment_id": "pay_01J...",
  "student_id": "stu_01J...",
  "amount_minor": 18000000,
  "currency": "MMK",
  "purpose": "course_fee",
  "status": "pending",
  "provider_name": null,
  "provider_transaction_id": null,
  "execution_id": "oia_exec_...",
  "created_at": "2026-10-22T00:00:00Z",
  "updated_at": "2026-10-22T00:00:00Z"
}
```

Timestamps are illustrative only. The implementation must generate UTC-aware timestamps from a trusted server clock. Never use these example IDs or timestamps as evidence.

## Minimal relational schema

Use the project's chosen supported database after checking deployment constraints. A relational schema is recommended because unique constraints and transactions are important. SQLite is acceptable for a local prototype or a single-host deployment with a confirmed persistent file path; do not treat a local SQLite file as a multi-host shared database.

### `payments`

| Column | Type / rule | Purpose |
|---|---|---|
| `payment_id` | TEXT primary key | Stable internal record ID |
| `student_id` | TEXT not null | Opaque internal student reference |
| `amount_minor` | INTEGER not null, CHECK > 0 | Exact amount |
| `currency` | CHAR(3) not null | ISO-style currency code; supported list configured explicitly |
| `purpose` | TEXT not null | Business reason / course fee category |
| `status` | TEXT not null, constrained enum | pending / confirmed / failed / refunded |
| `provider_name` | TEXT nullable | Exact configured provider |
| `provider_transaction_id` | TEXT nullable | Stable provider transaction ID |
| `execution_id` | TEXT nullable | Real OIA execution correlation |
| `created_at` | UTC timestamp text, not null | Creation audit |
| `updated_at` | UTC timestamp text, not null | Last state change |

Constraints:
- Unique `(provider_name, provider_transaction_id)` when provider transaction ID is present.
- Status changes are explicit and audited; a confirmed payment cannot silently be overwritten as pending.
- Use parameterized SQL, transactions and database constraints, not string-built SQL.

### `payment_events`

| Column | Type / rule | Purpose |
|---|---|---|
| `event_id` | TEXT primary key | Internal event ID |
| `payment_id` | TEXT foreign key | Related payment |
| `provider_name` | TEXT nullable | Event source |
| `provider_event_id` | TEXT nullable, unique per provider | Webhook idempotency/replay defense |
| `event_type` | TEXT not null | Provider event category |
| `observed_at` | UTC timestamp text, not null | Provider event time, after validation |
| `received_at` | UTC timestamp text, not null | Server receipt time |
| `verification_method` | TEXT not null | E.g. provider signature + API lookup; accurately describe actual method |
| `content_hash` | TEXT not null | Hash of canonical/raw event bytes according to documented rules |
| `raw_observation` | TEXT not null | Restricted-access raw provider observation; redact secrets/financial credentials |
| `execution_id` | TEXT nullable | Correlation when supported by the actual workflow |

Store secrets in a secret manager or protected runtime configuration, never in this table, Git, logs, issues or this document. Apply a retention and access policy to raw event data.

## Security requirements

- TLS for all non-local traffic; secure cookie/session or OAuth/service-token design chosen for the actual deployment.
- Authentication and role/tenant authorization on every route; least privilege for staff, backend service and OIA reader.
- Provider webhook signature validation against the exact provider's official documentation, constant-time comparison where applicable, timestamp tolerance, event ID deduplication and bounded body size.
- Request schema validation, positive integer amounts, explicit currency allowlist, safe status transition rules and parameterized queries.
- Rate limits, request IDs, bounded timeouts/retries and sanitized errors; never log access tokens, signatures, full payment credentials or unnecessary student PII.
- Idempotency for create and provider events; database unique constraints and atomic transactions.
- Secrets are injected at runtime and rotated; use separate test and production credentials.
- Audit every status transition with actor/source, timestamp, reason and correlation ID.
- Do not put full student identity or payment details in OIA's raw evidence unless strictly necessary.

## Required tests before connecting OIA

1. Create a valid pending payment; persist and retrieve it.
2. Reject missing/invalid student reference, non-positive amount, invalid currency and malformed fields.
3. Idempotent retry returns the same payment; same key/different payload returns conflict.
4. Concurrent duplicate provider transaction/event IDs are atomically rejected.
5. Unknown provider, invalid signature, stale/future event timestamp, malformed event and provider API timeout leave payment unconfirmed.
6. Amount/currency/merchant/payment-reference mismatch leaves payment unconfirmed and records a sanitized audit reason.
7. Unauthorized caller cannot create, read another tenant's payment or confirm a payment.
8. Invalid status transition is rejected; transaction rollback leaves no partial state.
9. Raw observation and normalized status remain separately inspectable; secret values are not present in logs.
10. OIA adapter rejects missing or mismatched `execution_id`, unknown source ID, stale receipt, invalid integrity and replay.
11. Verify SQLite persistence only on the intended persistent single-host file; if multi-host is required, test a shared transactional store with atomic unique claims instead.
12. Run `python -m unittest discover -s tests -v` and the repository's actual validation workflow on the exact commit; preserve logs and artifact provenance.

## OIA integration mapping (after the backend and provider contract exist)

| OIA field / check | Source mapping | Required behavior |
|---|---|---|
| `provider_name` | Exact configured provider identifier | Must be allowlisted; no caller-controlled arbitrary provider |
| `source_record_id` | Stable provider transaction ID or explicitly approved stable receipt ID | Must be retrieved from authoritative source |
| `execution_id` | Real `payments.execution_id` or separately versioned, auditable attribution record | Exact match; absent/mismatch fails closed |
| `raw_observation` | Verified provider event/API response, safely serialized | Keep separate from interpretation |
| `observed_at` | Provider timestamp with documented timezone semantics | Parse as timezone-aware UTC; reject stale/future/ambiguous |
| `content_hash` | Hash of the exact canonical/raw receipt bytes per documented algorithm | Recompute and compare; hash alone is not authenticity |
| `verification_method` | Actual signature/API verification method and version | Never claim a stronger method than executed |
| replay key | Provider + stable source record ID + content hash | Use existing replay store; durable store required for production |

Reuse `src/trusted_source_receipt.py`, the existing `TrustedSourceReceiptVerifier`, and the configured replay store. Add one provider-specific adapter only after official API documentation and the attribution model are available. A self-created EduAutomate database record is not, by itself, independent proof of payment settlement.

## Implementation sequence and release gates

1. **Owner decision:** confirm payment provider (or manual payment workflow), amount convention, tenancy/auth model and deployment target.
2. **Contract review:** review this proposal and resolve open questions; then add the chosen provider's official docs/schema.
3. **Backend slice:** implement database migrations/schema, create/read routes, idempotency, authorization, audit and OpenAPI.
4. **Provider verification:** implement only the documented provider event/API verification path; otherwise label manual evidence as internal attestation.
5. **Tests and CI:** implement the required tests and inspect the actual logs for the exact commit.
6. **OIA adapter:** map source records to existing typed receipt contract and test fail-closed/replay/attribution behavior.
7. **Evidence pilot:** independently inspect one genuine, redacted source-linked payment record and confirm execution attribution and provider authenticity.
8. **Release gate:** retain `EXEC-SUN-TRAVEL-005` on HOLD and keep release HOLD unless and until the relevant real source-linked evidence is independently verified. EduAutomate evidence must not be represented as evidence for SUN TRAVEL unless the actual workflow and source are the same.

## Open decisions (blocking implementation)

- Which payment provider is used, if any, and where are its official API/webhook docs?
- Are payments online-provider-confirmed, manually reconciled, or both?
- What is the exact MMK amount convention in the existing EduAutomate product?
- What framework, database, hosting target and identity/tenant model are intended?
- How does the chosen payment flow acquire a genuine OIA `execution_id`? Do not fabricate attribution.

## Current verified status

- Business backend: NOT BUILT (owner-confirmed).
- This file: contract proposal only.
- API implementation/OpenAPI generated from a running service: NOT BUILT.
- Provider-specific OIA adapter: BLOCKED on provider and API contract.
- Real payment evidence: NOT VERIFIED.
- Release: HOLD.
