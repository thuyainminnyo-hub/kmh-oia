# Operations & Infrastructure Specification — KMH OIA / EduAutomate

**Document status:** Proposed target specification / design record  
**Phase:** 950  
**Production status:** HOLD — this document is not deployment evidence or release approval.  
**Last updated:** 2026-10-23

## 1. Purpose and evidence boundary

This document records the Project Owner's target-host and persistent-database requirements. It does **not** assert that a host has been provisioned, a volume mounted, encryption enabled, backups configured, TLS enforced, RLS deployed, or any readiness gate tested. Each operational status must be supported by evidence from the actual target environment.

The inspected payment API prototype currently uses SQLite. PostgreSQL 15+ is a target decision and therefore requires a reviewed engine/schema migration plan; it is not an already completed migration.

## 2. Target application host / service

### Required target

- **Workload:** EduAutomate payment API and KMH OIA backend, containerized.
- **Production hosting:** Prefer a managed container service or Kubernetes with supported workload identity, secret integration, network policy, observability, rolling deployment, and rollback. Docker Compose may be used for local development or an explicitly approved limited deployment, but is not by itself evidence of enterprise production controls.
- **Environment isolation:** Separate production and staging accounts/projects/namespaces, credentials, network paths, databases, and data. Use synthetic data in staging unless a separately approved data-handling policy permits otherwise.
- **Container hardening:** Run as non-root; use minimal pinned images and dependency versions; scan images; use read-only root filesystem where feasible; drop unnecessary Linux capabilities; set resource requests/limits; do not bake secrets into images.
- **Secrets and identity:** Use a managed secret store and workload identity. No production secrets in source control, logs, PR comments, or this document.
- **Network:** Restrict database access to authorized application workloads; do not expose PostgreSQL directly to the public internet.
- **Observability:** Centralized structured logs, metrics, alerts, audit events, and deployment/version identifiers, with secrets and sensitive student/payment data redacted.

### Health and readiness

- `/healthz` is **liveness only**. It must not be treated as proof that the database or Registry is ready.
- A separate `/ready` endpoint may be introduced only with explicit, tested semantics. It must report not-ready when required database connectivity/schema checks or the authoritative Registry dependency are unavailable, according to the approved dependency policy.
- Readiness checks must not initialize or mutate the database, perform payment writes, leak credentials, or return sensitive dependency details.
- Startup, readiness, and shutdown behavior must be tested under database outage, Registry outage, missing storage, and recovery conditions.

## 3. API gateway / reverse proxy

- Use an approved NGINX or managed gateway / Cloudflare Gateway configuration appropriate to the deployment.
- Enforce HTTPS and TLS 1.3 for public client connections. Any internal hop that crosses a trust boundary must also use authenticated encryption; document and review any unavoidable TLS-version exception before release.
- Forwarded headers (including `X-Forwarded-For`) must be accepted only from explicitly trusted proxy hops. The edge proxy must strip client-supplied forwarding headers and set canonical values.
- **`X-Tenant-ID` is not an authentication or authorization credential.** Never trust a client-supplied tenant header as proof of membership. Derive tenant context from a verified identity and authoritative Registry membership; if the header is used as a routing hint, compare it against that trusted context and reject mismatches.
- Configure strict host/origin handling, request-size and rate limits, secure headers, access logging with sensitive-data redaction, and explicit CORS policy.
- Verify TLS policy, header sanitization, and tenant-header spoofing resistance with automated integration tests against the deployed gateway.

## 4. Persistent database specification

- **Target engine:** PostgreSQL 15 or later, with a currently supported minor release and an approved upgrade policy.
- **Storage:** Encrypted-at-rest high-availability persistent block storage (for example, cloud-provider managed persistent disk/EBS or an equivalent managed database storage tier). Select IOPS/throughput and capacity from measured workload and growth forecasts.
- **Preferred operations model:** A managed PostgreSQL service where it meets residency, networking, backup, access-control, and recovery requirements. If self-managed in a container, document ownership of storage, upgrades, failover, backups, monitoring, and recovery.
- **Container mount path if self-managed:** `/var/lib/postgresql/data`. Confirm the selected PostgreSQL image's supported data-directory layout and volume permissions. The mount path alone is not evidence that a persistent volume is attached.
- **Access control:** Separate application, migration, backup, and administrative roles with least privilege. Application credentials must not own tables or have RLS-bypass privileges.
- **Migration prerequisite:** The current prototype uses SQLite. Before PostgreSQL cutover, define and review a versioned schema/data migration, type/constraint mapping, downtime or dual-run strategy, idempotency and uniqueness behavior, reconciliation, rollback, and restore-tested recovery. Do not run production migration until approved.

## 5. Multi-tenancy and Row-Level Security (RLS)

- Persist a non-null `tenant_id` for every newly created tenant-owned payment and related tenant-scoped record once the authoritative Registry contract and identity adapter are approved.
- Existing records whose tenant ownership cannot be proven remain quarantined and inaccessible through tenant-authorized application paths. Do not infer ownership from request headers, student IDs, timestamps, or caller claims.
- Enable PostgreSQL RLS on every applicable tenant-owned table. Evaluate `FORCE ROW LEVEL SECURITY` where appropriate, and ensure the runtime application role does not own the tables and cannot bypass RLS.
- Set tenant context transaction-locally from the verified server-side identity/membership result; never set it directly from an untrusted header or request body.
- Enforce tenant scoping in application queries as defense in depth, including reads, writes, admin decisions, event/audit queries, and background jobs.
- Idempotency must be tenant-scoped (normally a reviewed composite constraint such as `(tenant_id, idempotency_key)`) after retry semantics and existing-key collisions are assessed.
- Acceptance tests must cover cross-tenant read/write/admin attempts, forged/missing tenant context, pooled-connection context leakage, background jobs, RLS bypass attempts, and legacy-row quarantine.

## 6. Backup, WAL, and recovery

- **Daily backups/snapshots:** At least every 24 hours, with a 30-day retention target, subject to the approved data-retention and compliance policy.
- **WAL archiving / PITR:** Enable and monitor PostgreSQL WAL archiving or the managed provider's equivalent continuous recovery mechanism.
- **Recovery objectives:** The owner must approve explicit RPO and RTO targets; do not infer them from the daily snapshot interval.
- **Restore validation:** Perform scheduled restore tests into an isolated environment, record the tested backup/WAL range, timestamp, database version, result, and recovery duration.
- Encrypt backups, restrict backup access, separate backup failure alerts from application alerts, and ensure deletion/retention controls are documented.
- Before schema migration: take a consistent backup, record table counts and checksums where feasible, restore-test it, and retain a reviewed rollback plan.

## 7. Fail-closed acceptance gates

Service must not accept payment reads/writes or privileged mutations when required persistent storage/database readiness, verified identity, authoritative tenant membership, or schema prerequisites are missing. Return a controlled not-ready/denied response without falling back to unscoped data or a weaker auth mode.

The following are required evidence, not presumed statuses:

| Component | Target requirement | Status at document creation |
|---|---|---|
| Container host/service | Production and staging isolated | **NOT VERIFIED** |
| Persistent database volume | Correct volume attached and mount verified from target host | **NOT VERIFIED** |
| Encryption at rest | Provider/storage configuration evidence | **NOT VERIFIED** |
| PostgreSQL 15+ | Provisioned, version recorded, migration reviewed | **NOT VERIFIED** |
| `/healthz` | Liveness only | Existing prototype contract; verify on target |
| `/ready` | Database/schema and Registry readiness semantics | **NOT VERIFIED / implementation required** |
| Fail-closed outage behavior | Tested with missing volume, DB outage, Registry outage | **NOT VERIFIED** |
| TLS 1.3 and proxy headers | Deployed config and external integration tests | **NOT VERIFIED** |
| Tenant RLS and scoped idempotency | Migration plus cross-tenant tests | **BLOCKED** on Registry/identity contract and schema review |
| Daily backup / 30-day retention | Configuration and backup evidence | **NOT VERIFIED** |
| WAL/PITR and restore | Recovery configuration and successful restore evidence | **NOT VERIFIED** |

## 8. Required evidence bundle before production approval

1. Target service/provider, environment identifier, deployed image digest, and exact code commit SHA.
2. Redacted infrastructure configuration showing isolated staging/production, TLS policy, gateway trust boundary, secret integration, and network restrictions.
3. Target-host evidence that the persistent volume/database is attached, with database version and storage/encryption settings. Do not include credentials or sensitive identifiers.
4. Exact-host tests for liveness/readiness and failure behavior with DB/storage/Registry unavailable.
5. Reviewed versioned SQLite-to-PostgreSQL migration plan, dry-run report, backup and restore evidence, rollback procedure, and reconciliation results.
6. Registry API contract and verified identity-to-tenant membership adapter.
7. RLS, tenant-scoped idempotency, legacy quarantine, and cross-tenant regression results.
8. Independent security review, resolution of findings, and explicit release-gate sign-off.

## 9. Release decision

**PRODUCTION HOLD.** This specification is a target design, not a claim that infrastructure is configured or mounted. No production migration, payment enablement, merge, or deployment is authorized by this document. Green CI or a local synthetic smoke test does not substitute for target-host evidence and independent review.
