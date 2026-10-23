# Phase 955 — FastAPI Tenant Context Dependency

Status: DRAFT IMPLEMENTATION CANDIDATE — NOT WIRED INTO PAYMENT ROUTES — PRODUCTION HOLD

## Why the supplied sketch was not copied verbatim

- Its mock Registry client returns True for most tenant IDs and uses substring checks for dead / timeout; that is not authorization and must never be treated as a production adapter.
- X-Tenant-ID is caller-controlled and cannot prove tenant membership.
- The Registry contract requires tenant_id and user_id; user identity must come from a server-verified identity assertion, not a caller-selected value or an assumed mapping from sub.
- Payment amount handling remains governed by the separate Whole-Kyat MMK decision; a float-based payment route must not be introduced.

## Implemented candidate

- src/tenant_context_dependency.py validates canonical tenant UUIDv4 format using the existing TenantContext model.
- It requires the tenant header to match the tenant claim from the existing verified identity dependency.
- It requires an explicit user_id claim in the trusted identity assertion and does not infer it from sub.
- It calls the existing fail-closed RegistryClient; explicit Registry denials map to HTTP 403 and availability/protocol failures map to HTTP 503.
- It emits generic error details rather than leaking exception messages.
- tests/test_tenant_context_dependency.py covers active membership, missing/malformed tenant context, header/claim mismatch, missing or malformed user identity, Registry denial, and Registry outage.

## Important limitations / gates

- Current identity-token verifier does not itself require a user_id claim; the dependency rejects requests without one. The identity-provider/claim contract must be confirmed before route integration.
- Tests use dependency overrides and synthetic Registry outcomes; they do not prove live Registry connectivity or production identity.
- This dependency is deliberately not attached to payment read/write/admin endpoints yet. The payment table still lacks persisted tenant_id, uses globally unique idempotency keys, and legacy ownership mapping is unavailable. Unknown legacy rows must remain quarantined.
- Before integration: confirm signed user_id claim with identity owner, obtain and validate authoritative legacy mapping, review tenant-scoped schema/idempotency migration, add route-level cross-tenant tests, obtain independent human review, and satisfy target-host evidence gates.

No database migration, data backfill, un-quarantine, payment-route enablement, merge, or deployment was performed.
