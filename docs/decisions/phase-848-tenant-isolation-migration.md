# Phase 848 — Tenant Isolation and Legacy Data Migration Decision Record

Status: DESIGN / OWNER DECISIONS REQUIRED — NOT IMPLEMENTED, NOT A RELEASE APPROVAL

## Evidence from the current prototype

Reviewed on branch `phase-823/payment-authz-hardening`, HEAD `bd4fced96d0de4e46313ba99b12f344eb3c2470c`.

- The `payments` table does not persist `tenant_id`.
- `idempotency_key` is globally unique today, not tenant-scoped.
- Identity mode intentionally fails closed for create/read/admin operations while tenant persistence and a reviewed identity-provider adapter are absent.
- Shared-token mode has no verified student-to-tenant membership and is restricted to local synthetic-data prototype use.
- Existing records cannot safely be assigned a tenant based on caller claims, student ID shape, timestamps, or guesswork.

## Required owner decisions before schema migration

Do not implement a tenant backfill until the product owner and data owner identify:

1. The authoritative tenant registry and immutable tenant identifier.
2. The authoritative student-to-tenant membership source, including how transfers and multiple memberships work.
3. The production identity provider and the verified mapping from subject to tenant and student membership.
4. The production admin identity/RBAC source and audit actor identity.
5. The database engine, migration tooling, maintenance window, backup, restore, rollback, and recovery-point requirements.
6. The policy for existing unscoped rows: archive/export, explicit verified mapping, or retention/deletion under an approved policy.

## Safe migration plan after decisions are approved

1. **Inventory and backup:** snapshot the database; record row counts and checksums; verify a restore into an isolated environment before changing schema.
2. **Expand schema:** add nullable `tenant_id` with a formal, versioned migration. Do not silently assign a default tenant.
3. **Quarantine legacy rows:** rows with unknown tenant ownership remain unscoped and inaccessible through tenant-authorized application routes. Do not infer ownership.
4. **Authoritative mapping:** populate tenant ownership only from a reviewed, reproducible mapping backed by the approved registry; record mapping provenance and exception counts.
5. **Scoped idempotency:** replace global uniqueness with a documented key scope, normally a composite uniqueness rule such as `(tenant_id, idempotency_key)`, after confirming the desired retry semantics and resolving existing collisions. Use a migration that detects and reports collisions before adding the constraint.
6. **Scoped authorization:** create operations derive tenant/student identity from the verified identity adapter and authoritative membership—not caller-provided request fields. Reads and admin decisions query by both tenant scope and record ID, with authorization before any data is returned. Admin access requires individual identity and explicit role/policy checks.
7. **Audit integrity:** record the authenticated actor, tenant, action, request correlation ID, and policy decision. A hash stored in the same database is not independently tamper-proof evidence.
8. **Dual verification:** test cross-tenant read denial, create membership enforcement, admin privilege boundaries, tenant-scoped idempotency, duplicate/collision behavior, and legacy-row denial. Include negative tests that prove no record lookup occurs after an authorization failure.
9. **Recovery rehearsal:** test backup restore, migration rollback or forward-fix procedure, interrupted migration recovery, and concurrent request behavior against the target database.
10. **Independent review and release gate:** obtain a reviewer independent of the PR author; verify CI on the exact final commit; keep release HOLD until all owner decisions, deployment controls, and evidence gates are closed.

## Required acceptance evidence

- Approved tenant and identity data-source decision.
- Versioned migration plus reviewed rollback/recovery procedure.
- Before/after row counts, mapping exception report, and collision report.
- Passing cross-tenant and role-boundary regression tests.
- Successful isolated restore/recovery rehearsal.
- Independent human review and release-gate sign-off.

## Current decision

**HOLD — no tenant schema migration is safe to apply yet.** The missing authoritative ownership source is a product/data decision, not something the implementation should guess. Existing identity-mode fail-closed behavior must remain until the approved design is implemented and verified.
