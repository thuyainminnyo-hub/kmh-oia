# Phase 953 — Tenant-scoped persistence and migration plan

Status: DESIGN-ONLY DRAFT — NO MIGRATION EXECUTED — PRODUCTION HOLD

## Purpose

Prepare a reviewable migration plan before Registry authorization is connected to payment routes. The current prototype uses SQLite, has no `payments.tenant_id`, and declares `idempotency_key TEXT NOT NULL UNIQUE`. A Registry check alone cannot make payment records tenant-safe when ownership is not persisted and idempotency remains globally scoped.

## Non-negotiable invariants

1. Never infer a payment's tenant from `student_id`, amount, currency, purpose, timestamps, or caller-provided headers.
2. Never assign a default tenant to legacy records.
3. Any row whose tenant ownership cannot be established from an authoritative, auditable source remains quarantined and inaccessible through ordinary payment routes.
4. Idempotency scope must include tenant identity; same key in different tenants must not collide, while same tenant + same key + same canonical request must replay safely and a different request must conflict.
5. Registry timeout, transport failure, non-200 other than explicit deny, malformed response, inactive tenant/member, and mismatched returned IDs must never authorize a payment operation.
6. All read, create, replay, admin decision, and audit/event access paths must be tenant scoped. An unscoped route remains disabled.
7. No production migration, deployment, data backfill, or payment enablement is authorized by this plan.

## Proposed reviewed migration stages

### Stage 0 — Inventory and freeze

- Identify every route, query, event, replay path, admin action, fixture, export, and reporting query touching payments.
- Record SQLite schema version, row counts, status counts, idempotency collision counts, database file identity, and a cryptographic checksum of a read-only snapshot.
- Identify all consumers of the current `amount_minor` field separately; the approved MMK unit is whole Kyats, but this tenant migration must not silently rename or reinterpret amounts.
- Preserve the original database and ensure a restore rehearsal is completed before any mutation.

### Stage 1 — Define ownership evidence

- Require a Master Registry owner-controlled, auditable mapping that establishes the authoritative tenant for each legacy payment/student identity.
- Validate mapping provenance and cardinality; ambiguous, missing, or conflicting mappings are exceptions, not automatic assignments.
- Produce a dry-run report with counts: verified assignable, quarantined unknown, quarantined ambiguous, invalid mapping, and orphaned event records.
- A human owner must approve the mapping and exception report before any data write.

### Stage 2 — Schema and idempotency design

- Add explicit tenant ownership to payment records and relevant event/audit records, with constraints appropriate to the final schema.
- Replace global idempotency uniqueness with a reviewed tenant-scoped uniqueness model. SQLite requires a table rebuild to remove the existing inline global UNIQUE constraint; do not assume adding an index cancels it.
- Define canonical request fingerprint semantics, tenant-scoped unique constraints, conflict/replay response behavior, and transaction boundaries.
- Design migration as versioned, restart-safe, transactional where SQLite permits, with preconditions and postconditions. No blind `ALTER TABLE` or implicit default tenant.
- Keep unknown-ownership records in a restricted quarantine table or immutable quarantine artifact; ordinary routes must not read or mutate them.

### Stage 3 — Offline rehearsal

- Run migration only against a disposable copy of the snapshot using synthetic or approved de-identified data.
- Compare before/after row counts, per-status counts, checksums for immutable fields, event foreign keys, tenant assignments, quarantine counts, and idempotency collisions.
- Prove rollback and restore from backup. Record exact code SHA, schema version, tool version, UTC time, input snapshot checksum, and generated report.
- Abort on any unexplained count/hash difference, ownership ambiguity, or failed restore.

### Stage 4 — Route integration (separate reviewed change)

- Obtain verified identity from the approved authentication layer; never trust `X-Tenant-ID` alone as identity or authorization.
- Call Registry for the exact authenticated user + requested tenant and accept only a matching HTTP 200 with both tenant and membership ACTIVE.
- Scope SQL reads, creates, replay lookups, admin decisions, event retrieval, and audit queries to the verified tenant context.
- Use the verified tenant ID in idempotency key scope and payment persistence; never accept a tenant ID from an untrusted body as sufficient authority.
- Add cross-tenant negative tests for guessed payment IDs, replay-key collisions, read/list endpoints, admin actions, events, and mismatched Registry responses.
- Keep identity-mode operations fail-closed until the full suite and independent review pass.

### Stage 5 — Release evidence gate

Required before a release decision:
- Approved migration diff and dry-run report.
- Independent reviewer approval of schema, migration, authorization, and tests.
- Exact-head CI pass.
- Verified backup and restore rehearsal.
- Live Registry contract test using owner-controlled test credentials/environment (never commit or paste secrets into GitHub/Notion).
- Target-host evidence and rollback plan under Issue #101.
- Explicit owner approval for any production migration/deployment.

## Open owner decisions

- What authoritative source maps existing `student_id` / legacy payment records to Registry tenant ownership?
- Are payment records globally unique identifiers, and what are the expected retention/audit obligations for quarantined rows?
- What is the final database target for this migration: keep SQLite for a controlled prototype, or separately plan PostgreSQL migration? Do not combine a tenant migration and SQLite-to-PostgreSQL migration without explicit design/review.
- Which identity provider supplies the authenticated `user_id` and how is that identity bound to the Registry request?
- Which roles may create, read, replay, confirm, or reject payments within a tenant?

## Current evidence boundary

The Registry adapter's synthetic unit tests do not prove live Registry connectivity. The current schema lacks tenant ownership and has global idempotency uniqueness. This document is a plan only; no database was opened, modified, migrated, or backfilled.

Production remains HOLD.
