# Phase 849 — Production Tenant and Payment Owner Decisions

Status: UNDECIDED — OWNER INPUT REQUIRED — RELEASE HOLD

This worksheet makes the product/data decisions blocking tenant isolation explicit. Do not fill fields with assumptions. A decision is accepted only when the named owner and evidence/source are recorded.

## Decision register

| ID | Decision required | Accepted answer must identify | Current status |
|---|---|---|---|
| D-01 | Tenant authority | Registry/system of record, immutable tenant ID, owner, lookup contract | APPROVED WITH CONDITIONS — design-level only; live lookup contract NOT ESTABLISHED |
| D-02 | Student membership | Authoritative student-to-tenant membership source, multi-membership/transfer rules, revocation timing | UNDECIDED |
| D-03 | Identity provider | Provider, issuer, audience, signing-key/JWKS validation strategy, subject-to-member mapping, token expiry/rotation | UNDECIDED |
| D-04 | Admin authorization | Individual admin identity source, role assignment/approval process, separation of duties, emergency access | UNDECIDED |
| D-05 | Legacy payment records | Approved mapping source or quarantine/archive/retention policy for rows with no verified tenant | UNDECIDED |
| D-06 | Database and migration | Target database, versioned migration framework, maintenance/locking strategy, rollback/forward-fix plan | UNDECIDED |
| D-07 | Idempotency semantics | Whether keys are scoped per tenant, per student, or another explicit scope; retry retention and conflict behavior | UNDECIDED |
| D-08 | Amount unit | Whether `amount_minor` means MMK kyat, pya, or another defined minor unit; API display conversion and rounding rules | UNDECIDED |
| D-09 | Payment confirmation evidence | Whether confirmation is manual attestation or provider/bank-verified settlement; evidence source and reconciliation owner | UNDECIDED |
| D-10 | Recovery objective | Backup frequency, recovery point/time objectives, restore owner, evidence required to approve recovery | UNDECIDED |
| D-11 | Audit and retention | Required audit fields, tamper-evidence/storage, retention/deletion rules, privacy owner | UNDECIDED |

## Decision capture template

For each ID, record:

- **Decision:** `PENDING`
- **Accountable owner:** `NOT ASSIGNED`
- **Authoritative source / evidence:** `NOT PROVIDED`
- **Decision date:** `NOT SET`
- **Security/data impact reviewed by:** `NOT REVIEWED`
- **Implementation acceptance test:** `NOT DEFINED`

## Implementation rule

Until the relevant decisions are approved:
- Keep identity-mode create/read/admin operations fail-closed.
- Do not infer tenant ownership for legacy records.
- Do not assign a default tenant or relax tenant authorization.
- Do not claim bank settlement based on a manual internal status.
- Do not change the amount unit or uniqueness semantics without a migration and compatibility plan.
- Keep the release gate on HOLD.

## Exit criteria

The worksheet is not complete until every applicable decision has an accountable owner, cited source/evidence, approved value, and corresponding test or operational verification. Only then may implementation proceed through a reviewed migration, cross-tenant negative tests, recovery rehearsal, independent human review, and exact-commit CI verification.


## Phase 860 — JWT Time-Claim Boundary Test Record

Status: TESTED IN CI — PROTOTYPE ONLY — RELEASE HOLD

The prototype verifier now rejects optional `nbf` values that are malformed or in the future, optional `iat` values that are malformed or in the future, and Boolean values supplied for `exp`. Regression tests assert HTTP 401 before payment-storage access for future `nbf`, future `iat`, malformed `nbf`, Boolean `iat`, and Boolean `exp`.

Exact candidate commit: `b9388a33bd3a5ada85fca9cc38442bd98d52f511`

- Tests #892: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/39783608452 — SUCCESS
- Validation #811: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/39783608749 — SUCCESS

This record is regression evidence for the isolated local verifier only. It is not approval of a production token-validation design. The production identity provider, OIDC/JWKS integration, key rotation, authoritative tenant/student membership, tenant-scoped persistence, and independent review remain unresolved. Do not treat these tests as proof of tenant isolation or production readiness.

## Phase 940 — D-01 owner response and Registry contract gate

Decision record date: 2026-10-23  
Accountable owner: Pyi Naing  
Decision status: **APPROVED WITH CONDITIONS — INTERNAL SOLO ARCHITECTURE SIGN-OFF ONLY**  
Production status: **HOLD**

### Accepted design decisions

- **Source of truth:** Master System / Central Registry. Do not create a separate KMH OIA Tenant Registry.
- **Canonical tenant identifier:** `tn_` followed by a lowercase canonical UUIDv4.
- **Membership authority:** the Master System's student-enrollment/membership mapping is the intended authority.
- **Legacy data:** payment rows without a verified ownership mapping must be quarantined; do not infer or auto-fill tenant ownership from student IDs, caller claims, timestamps, or other heuristics.

### Explicit unresolved boundary

The actual external Registry API endpoint, schema, authentication method, error semantics, membership lookup contract, and runtime connectivity have **NOT BEEN ESTABLISHED**. The intended membership source is not proof that a usable integration exists.

Until a versioned contract is supplied and verified:
- use only a mock/abstract adapter interface in development;
- fail closed when authoritative membership cannot be established;
- do not enable identity-mode payment reads, writes, or admin mutations;
- do not migrate or backfill tenant ownership;
- do not treat canonical tenant syntax as proof of tenant existence or membership.

### Gate B — implementation prerequisites

Before production implementation, capture and review:
1. Registry owner and authoritative API/specification reference.
2. Endpoint and version, request/response schema, and tenant/student membership semantics (including transfer, multiple membership, revocation, and not-found behavior).
3. Authentication/authorization method, credential handling, timeout/retry policy, and key/credential rotation.
4. Error mapping and fail-closed behavior for unavailable, malformed, stale, or ambiguous responses.
5. A verified subject-to-student-to-tenant mapping path; caller-supplied tenant claims alone are insufficient.
6. Contract tests using approved fixtures plus negative tests proving no payment database access after failed membership authorization.

### Gate C — verification and release evidence

Production remains HOLD until the following are evidenced on the exact candidate commit:
- tenant-scoped persistence and tenant-scoped idempotency with migration/collision handling;
- legacy-row quarantine and a tested backup/restore/rollback or forward-fix procedure;
- cross-tenant read/write/admin denial tests, including no-lookup assertions on denied requests;
- Registry contract and adapter verification against the authoritative source;
- independent human review and explicit release-gate approval.

This owner response resolves the **design direction** for D-01 only. It does not establish the live Registry API contract, complete D-02 through D-11, prove implementation, constitute independent review, or authorize production release.
