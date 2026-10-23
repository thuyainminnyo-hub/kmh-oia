# Phase 952 — Master Registry Contract Adapter

Status: IMPLEMENTATION CANDIDATE IN DRAFT PR — SYNTHETIC TESTS ONLY — PRODUCTION HOLD

## Contract adopted for this adapter

- POST /api/v1/registry/tenants/verify
- Authorization: Bearer <service-to-service token>
- JSON request: tenant_id, user_id
- HTTP 200: accept only when returned tenant and user exactly match the request and tenant and membership statuses are both ACTIVE.
- HTTP 403 / 404: explicit deny.
- Timeout, transport failure, HTTP 503, other non-200 statuses, malformed JSON, schema mismatch, inactive state, or mismatched IDs: never grant access. Availability/protocol failures raise RegistryUnavailable; explicit denial raises RegistryDenied.
- Tenant ID syntax requires tn_ plus a canonical lowercase UUIDv4. Syntax is not proof of tenant existence or membership.
- User ID syntax follows usr_ plus canonical UUID-shaped hex segments; authority still comes only from Registry.

## Files in this candidate

- src/registry_client.py: Pydantic request/response models and fail-closed HTTP adapter.
- tests/test_registry_client.py: synthetic HTTP transport tests for allow, explicit deny, timeouts, network errors, unexpected status, malformed response, identity mismatch and malformed tenant IDs.
- tests/fixtures/registry_membership_scenarios.json: supplied scenario shapes retained as explicitly synthetic data.

## Integration boundary — deliberately not crossed yet

This candidate does not wire Registry checks into payment read/write/admin routes. Doing so safely also requires tenant ownership persisted on payment records, tenant-scoped idempotency, tenant-scoped reads/admin actions, a reviewed schema migration and explicit legacy-row quarantine. The current SQLite prototype schema lacks tenant_id and uses globally unique idempotency keys. Enabling routes before those prerequisites would risk cross-tenant data exposure or incorrect idempotency behavior.

## Required before production

1. Confirm live service URL, TLS trust, service-token issuance/rotation and Registry owner's error response schema (including whether 403/404 include stable error codes).
2. Independently verify the contract against the actual Registry service or owner-controlled contract tests; local mocks are not live-service evidence.
3. Add reviewed tenant persistence and tenant-scoped idempotency migration with dry-run, backup/restore rehearsal and legacy rows quarantined when ownership is unknown.
4. Add route-level cross-tenant negative tests and ensure reads, writes, admin actions and replay all verify membership.
5. Run exact-head CI, obtain independent human review and collect target-host evidence. Do not merge or deploy from this draft alone.

Production remains HOLD. No production data was read or changed by this implementation.
