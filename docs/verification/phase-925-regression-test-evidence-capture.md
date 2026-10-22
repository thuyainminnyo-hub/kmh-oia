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
| REG-01 | Missing API token fails closed | NOT RUN for this phase | Exact-commit unit-test result and assertion output |
| REG-02 | Wrong API token is rejected | NOT RUN for this phase | Exact-commit unit-test result and assertion output |
| REG-03 | Missing shared-token prototype opt-in blocks writes before persistence | NOT RUN for this phase | Test output plus database row-count assertion |
| REG-04 | Identity mode rejects invalid signature before payment lookup | NOT RUN for this phase | Test output showing lookup mock was not called |
| REG-05 | Wrong issuer/audience and invalid time claims fail closed | NOT RUN for this phase | Exact-commit test output |
| REG-06 | Identity-mode read remains blocked until tenant scope is persisted | NOT RUN for this phase | HTTP response assertion and lookup mock not called |
| REG-07 | Registry timeout/unavailable/malformed response | BLOCKED | Registry adapter and contract must exist first |
| REG-08 | Cross-tenant read/write/admin denial | BLOCKED | Approved tenant source, persisted tenant scope, and tenant-aware authorization |
| REG-09 | Same idempotency key in different tenants is independent | BLOCKED | Tenant-scoped schema and uniqueness contract |
| REG-10 | Legacy row with unknown owner is quarantined | BLOCKED | Approved legacy-data policy and migration tooling |
| REG-11 | Existing API regression suite | NOT RUN for this phase | CI run URL, exact head SHA, final job status |
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
