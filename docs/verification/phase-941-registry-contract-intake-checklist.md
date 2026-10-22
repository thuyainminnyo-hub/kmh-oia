# Phase 941 — Registry Contract Intake and Adapter Acceptance Checklist

Status: INTAKE TEMPLATE — CONTRACT NOT PROVIDED — NOT IMPLEMENTED — RELEASE HOLD

## Purpose

Collect authoritative evidence needed to implement the Master System / Central Registry membership adapter without inventing endpoints, schemas, credentials, or authorization behavior. This document is a checklist, not an API specification.

## Current known decision

- Intended source of truth: Master System / Central Registry.
- Canonical tenant ID format: `tn_` followed by lowercase canonical UUIDv4.
- Intended membership authority: Master System student-enrollment/membership mapping.
- External Registry API endpoint, schema, authentication method, and runtime contract: **NOT ESTABLISHED**.
- Production release: **HOLD**.

## Required source material — owner or Registry team must supply

Record the exact authoritative document or approved system reference for each item. Do not replace unknowns with assumptions.

| Field | Required evidence | Status |
|---|---|---|
| Registry owner/contact | Accountable team and technical owner | NOT PROVIDED |
| API specification | Versioned OpenAPI/schema or equivalent authoritative contract | NOT PROVIDED |
| Base URL/environment | Approved development/staging endpoint and production endpoint reference | NOT PROVIDED |
| Authentication | Approved auth mechanism, audience/scope, credential storage and rotation policy | NOT PROVIDED |
| Tenant lookup | Request/response fields and canonical tenant identity semantics | NOT PROVIDED |
| Student membership lookup | Subject/student/tenant mapping and membership status semantics | NOT PROVIDED |
| Multiple memberships/transfers | Rules for multiple tenants, transfer, suspension, and revocation | NOT PROVIDED |
| Error semantics | Distinguish not found, denied, unavailable, timeout, malformed response, and ambiguous result | NOT PROVIDED |
| Freshness/revocation | Cache policy and maximum acceptable membership staleness | NOT PROVIDED |
| Reliability limits | Timeout, retry/backoff, rate limits, circuit-breaker expectations | NOT PROVIDED |
| Audit/privacy | Permitted logged fields, correlation IDs, retention and sensitive-data rules | NOT PROVIDED |
| Test fixtures | Approved synthetic positive and negative contract fixtures | NOT PROVIDED |

## Adapter implementation acceptance criteria — blocked until contract is approved

1. Derive caller identity from a verified identity provider; do not trust request-supplied tenant/student IDs as proof of membership.
2. Resolve membership using the approved Registry contract and documented policy.
3. Fail closed on timeout, unavailable service, invalid signatures/credentials, malformed or ambiguous responses, unknown membership, or revoked membership.
4. Do not initialize or query payment storage when identity/membership authorization fails.
5. Apply documented timeout/retry rules; retries must not turn an authorization uncertainty into an allow decision.
6. Avoid logging tokens, credentials, bank-slip contents, or unnecessary personal data.
7. Keep the adapter interface mockable for unit tests, but clearly label mock results as test-only and never as production verification.
8. Add contract tests and integration tests against an approved non-production Registry environment before claiming integration is verified.

## Required negative tests

- Unknown tenant ID.
- Valid tenant syntax but nonexistent tenant.
- Authenticated subject with no student membership.
- Student belongs to Tenant A and attempts to access Tenant B.
- Membership revoked or suspended.
- Registry timeout/unavailable response.
- Malformed or incomplete Registry response.
- Credential failure / unauthorized Registry response.
- Ambiguous multiple membership when policy does not resolve it.
- Every denied/indeterminate case asserts no payment database lookup or mutation.

## Exit gate

Gate B cannot start until the authoritative contract and identity-to-membership mapping are supplied and reviewed. Gate C cannot pass until tenant-scoped persistence/idempotency, legacy-row quarantine, migration/recovery rehearsal, cross-tenant negative tests, exact-commit CI, and independent human review are evidenced.

**No schema migration, legacy backfill, identity-mode payment read/write enablement, or production release is authorized by this checklist.**
