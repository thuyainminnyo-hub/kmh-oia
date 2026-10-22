# Phase 925 — Regression Test Evidence Capture

**Status:** TEST PLAN / EVIDENCE REGISTER — NOT A TEST RUN, NOT A RELEASE APPROVAL

## Scope

This phase defines how regression-test outcomes are recorded against an exact repository commit. It does not claim that tests were run, does not add tenant isolation to the payment API, and does not authorize migration or deployment.

Baseline reviewed: `a482adb0541729ce9638d0c9692dd1662e9a3210` on PR #103. Re-check the branch head before interpreting any CI result.

## Evidence status vocabulary

- **PASS** — command/workflow completed successfully for the recorded commit and the expected assertion is visible in its output.
- **FAIL** — command/workflow completed and one or more required assertions failed.
- **BLOCKED** — the behavior cannot yet be tested because a prerequisite implementation/decision is absent.
- **NOT RUN** — no execution evidence has been captured.
- **NOT APPLICABLE** — explicitly justified and approved for the scoped test.

Never convert NOT RUN or BLOCKED to PASS based on design notes, a previous commit's CI, or an expected result.

## Regression evidence matrix

| ID | Scenario | Current status | Evidence required |
|---|---|---|---|
| REG-01 | Missing API token fails closed | PASS — exact-commit CI #899 | `test_payment_read_requires_api_token`; see exact-commit test log below |
| REG-02 | Wrong API token is rejected | PASS — exact-commit CI #899 | `test_api_requires_configured_token_and_rejects_bad_token`; see exact-commit test log below |
| REG-03 | Missing shared-token prototype opt-in blocks writes before persistence | NOT RUN for this phase | Test output plus database row-count assertion |
| REG-04 | Identity mode rejects invalid signature before payment lookup | PASS — exact-commit CI #899 | `test_identity_mode_rejects_bad_signature_before_payment_storage_access`; see exact-commit test log below |
| REG-05 | Wrong issuer/audience and invalid time claims fail closed | PASS — existing claim-validation tests in CI #899 | Named issuer, audience, `exp`, `nbf`, and `iat` regression tests are listed below; this is prototype-verifier coverage, not production IdP validation |
| REG-06 | Identity-mode read remains blocked until tenant scope is persisted | PASS — exact-commit CI #899 | `test_identity_mode_disables_reads_until_tenant_scope_is_persisted` and `test_identity_mode_denies_before_payment_lookup`; see exact-commit test log below |
| REG-07 | Registry timeout/unavailable/malformed response | BLOCKED | Registry adapter and contract must exist first |
| REG-08 | Cross-tenant read/write/admin denial | BLOCKED | Approved tenant source, persisted tenant scope, and tenant-aware authorization |
| REG-09 | Same idempotency key in different tenants is independent | BLOCKED | Tenant-scoped schema and uniqueness contract |
| REG-10 | Legacy row with unknown owner is quarantined | BLOCKED | Approved legacy-data policy and migration tooling |
| REG-11 | Existing API regression suite | PASS — 495 tests in CI #899 | Exact head SHA, run URL, final output and limitations recorded in the post-authoring evidence section below |
| REG-12 | Migration/rollback rehearsal | BLOCKED | Owner decisions, disposable database fixture, backup/restore and rollback plan |

## Required evidence bundle for each executed test

Record:
1. Test ID and test name.
2. Repository and exact commit SHA.
3. Command or workflow URL.
4. Final exit status and relevant assertion/output.
5. Database side-effect check, when applicable.
6. Reviewer/owner, timestamp, and unresolved issue.
7. Classification: PASS, FAIL, BLOCKED, NOT RUN, or NOT APPLICABLE.

Do not include secrets, tokens, student personal information, raw bank-slip data, or production payment data in logs or artifacts.

## Entry and exit gates

### Entry gate
- [ ] Confirm the exact branch head and source files.
- [ ] Use isolated temporary test data only.
- [ ] Preserve all existing fail-closed tests.
- [ ] Identify prerequisites for every BLOCKED test.

### Exit gate
- [ ] Run the existing unit suite against the exact candidate commit.
- [ ] Capture CI run links and commit SHA.
- [ ] Record failures without hiding or reclassifying them.
- [ ] Keep tenant isolation tests BLOCKED until tenant-aware implementation exists.
- [ ] Obtain independent review of changes and evidence.
- [ ] Keep PR #103 and production release on HOLD until all owner and review gates are satisfied.

## Current disposition

No tests were run as part of authoring this document. The historical CI successes for a prior candidate are not proof of a new run or of tenant isolation. D-01 and dependent owner decisions remain unresolved in the currently verified evidence. No schema migration, tenant backfill, authorization broadening, merge, or deployment is authorized by this phase.


## Post-authoring CI evidence update (2026-10-22)

This update records CI that ran **after** the original document commit was authored. It does not change the original statement that no tests were run as part of authoring the initial document.

- Exact tested commit: `859183dfc78c00220e2a9799b95f56a4f23d6097`
- Tests workflow #899: SUCCESS — https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/39871981366
- Validation workflow #818: SUCCESS — https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/39871981364
- Test job output: `Ran 495 tests`; final output `OK`.
- Validation job steps completed successfully: `compileall`, `scripts/deployment_preflight.py`, readiness snapshot generation, `git diff --check`, and unittest discovery.

Observed passing API test names in the exact-commit log include:
- `test_payment_read_requires_api_token`
- `test_api_requires_configured_token_and_rejects_bad_token`
- `test_identity_mode_rejects_bad_signature_before_payment_storage_access`
- `test_identity_mode_rejects_wrong_issuer_before_payment_storage_access`
- `test_identity_mode_rejects_wrong_audience_before_payment_storage_access`
- `test_identity_mode_rejects_boolean_exp_before_payment_storage_access`
- `test_identity_mode_rejects_future_not_before_before_payment_storage_access`
- `test_identity_mode_rejects_future_issued_at_before_payment_storage_access`
- `test_identity_mode_rejects_malformed_not_before_before_payment_storage_access`
- `test_identity_mode_disables_reads_until_tenant_scope_is_persisted`
- `test_identity_mode_denies_before_payment_lookup`

REG-03 remains NOT RUN for this evidence register because the required explicit database row-count/side-effect evidence has not been separately recorded here. REG-07 through REG-10 and REG-12 remain BLOCKED. Passing existing prototype tests does not implement or prove tenant isolation, a Registry integration, production identity/RBAC, real settlement verification, migration safety, or deployment readiness.
