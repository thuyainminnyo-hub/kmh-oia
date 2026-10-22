# Phase 850 — Tenant Isolation Verification Matrix

Status: PRE-MIGRATION SAFETY MATRIX — NOT A PRODUCTION APPROVAL

This matrix turns the Phase 848 migration plan and Phase 849 owner decisions into verifiable gates. Tests marked **BLOCKED** require the authoritative sources and schema decisions to be approved first. Do not treat a passing prototype test as evidence that production tenant isolation is implemented.

## A. Safety invariants testable before migration

| ID | Scenario | Expected result | Status |
|---|---|---|---|
| PRE-01 | Identity-mode create with a syntactically valid token and tenant claim while tenant persistence is absent | Fail closed; no payment row inserted | Existing test coverage reported; rerun on target HEAD |
| PRE-02 | Identity-mode read for student role, admin role, tenant A, or tenant B while tenant persistence is absent | Fail closed before payment lookup; no payment data returned | Existing test coverage reported; rerun on target HEAD |
| PRE-03 | Identity-mode admin decision before verified adapter and tenant schema exist | Fail closed; no payment status or audit mutation | Existing test coverage reported; rerun on target HEAD |
| PRE-04 | Shared-token writes without explicit prototype opt-in | Fail closed; no payment row inserted | Existing test coverage reported; rerun on target HEAD |
| PRE-05 | Production environment | Generated OpenAPI, Swagger, and ReDoc routes disabled | Existing test coverage reported; rerun on target HEAD |

## B. Required acceptance tests after owner decisions and migration

| ID | Scenario | Required assertion | Gate |
|---|---|---|---|
| TEN-01 | Tenant A student creates a payment for their own verified membership | Persisted tenant/student scope comes from verified identity/membership, not untrusted request fields | BLOCKED: D-01–D-03 |
| TEN-02 | Student submits another student's ID in same tenant | Denied unless authoritative policy explicitly grants this capability; no row created | BLOCKED: D-02 |
| TEN-03 | Tenant A caller requests Tenant B payment ID | Denied without revealing existence or payment details | BLOCKED: D-01–D-03 |
| TEN-04 | Tenant A admin attempts to confirm Tenant B payment | Denied; status and audit rows remain unchanged | BLOCKED: D-01–D-04 |
| TEN-05 | Non-admin identity attempts admin decision | Denied; no mutation | BLOCKED: D-03–D-04 |
| IDEM-01 | Same key and same payload retried within approved scope | Return the original operation result according to the documented retry contract | BLOCKED: D-07 |
| IDEM-02 | Same key with a different payload in the same approved scope | Deterministic conflict; no second payment row | BLOCKED: D-07 |
| IDEM-03 | Same key reused by separate tenants | Behavior matches the approved scope; no cross-tenant record disclosure | BLOCKED: D-01, D-07 |
| LEG-01 | Legacy payment has no verified tenant mapping | Row is quarantined/unavailable through tenant-authorized routes | BLOCKED: D-05 |
| MIG-01 | Migration encounters duplicate keys under proposed scoped uniqueness | Migration emits a collision report and does not silently discard or reassign records | BLOCKED: D-06–D-07 |
| MIG-02 | Migration is interrupted or rollback/forward-fix is invoked | Recovery follows rehearsed procedure and preserves records; evidence is retained | BLOCKED: D-06, D-10 |
| AUD-01 | Successful and denied payment/admin operations | Audit records authenticated actor, tenant, action, correlation, and policy result without leaking secrets | BLOCKED: D-04, D-11 |
| PAY-01 | Payment status is set to confirmed | UI/API labels it as an internal admin attestation unless independently reconciled against bank/provider settlement | BLOCKED: D-09 |
| AMT-01 | Amount is accepted and displayed | API contract and conversions consistently follow the approved MMK unit and rounding policy | BLOCKED: D-08 |

## C. Evidence bundle required for release review

1. Approved Phase 849 decision register, with accountable owner and evidence for each applicable decision.
2. Versioned migration, schema diff, pre/post row counts, tenant mapping provenance, and collision report.
3. Automated test results for all TEN, IDEM, LEG, MIG, AUD, PAY, and AMT cases.
4. Backup restore, interrupted migration, rollback/forward-fix, and recovery rehearsal logs.
5. Exact commit SHA with all required CI checks completed successfully.
6. Independent human review and explicit release-gate sign-off.

## Release rule

The matrix is a plan, not proof that blocked scenarios pass. Keep Release HOLD until the blocked prerequisites are resolved, implementation and tests are reviewed, and the evidence bundle is accepted. CI success alone does not establish production readiness or payment settlement.
