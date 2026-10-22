# Phase 849 — Production Tenant and Payment Owner Decisions

Status: UNDECIDED — OWNER INPUT REQUIRED — RELEASE HOLD

This worksheet makes the product/data decisions blocking tenant isolation explicit. Do not fill fields with assumptions. A decision is accepted only when the named owner and evidence/source are recorded.

## Decision register

| ID | Decision required | Accepted answer must identify | Current status |
|---|---|---|---|
| D-01 | Tenant authority | Registry/system of record, immutable tenant ID, owner, lookup contract | UNDECIDED |
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
