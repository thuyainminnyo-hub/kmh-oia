# Rollback Plan — Agent Identity & Delegated Authorization V1

## Safety boundary

- Target is the disposable branch `disposable/agent-identity-authorization-v1` only.
- Frozen starting point: `132d6a09a6b91030835c07e5ff129eeeb79c4fba`.
- Never reset, force-push, amend, or write to `main`.
- Do not modify existing branches or pull requests.
- No merge, deployment, live identity-provider integration, credential use, protected tool execution, or production data access.

## Rollback triggers

Stop and quarantine this candidate if any of the following occurs:

1. A test demonstrates cross-tenant authorization or an unexpected ALLOW.
2. A delegated request is allowed with a revoked, expired, not-yet-valid, wrong-audience, wrong-subject, or insufficient-scope grant.
3. A policy-version mismatch or missing identity context does not fail closed.
4. The candidate changes an out-of-scope file or touches an existing branch/PR.
5. Test execution is non-reproducible or the evidence cannot be tied to the exact commit.

## Rollback procedure

1. Stop further writes to the disposable branch.
2. Preserve the candidate head SHA, commit list, test output, and relevant CI run links in the evidence ledger.
3. Do not move or force-update any ref.
4. For a clean retry, create a new disposable branch from the then-current, re-verified `main` SHA; do not reuse a stale base.
5. If the candidate must be neutralized on the same branch, use a reviewed revert commit on that disposable branch only. Do not delete history.
6. Re-run the full synthetic regression suite on the resulting exact head.
7. Require independent QA and fresh human approval before any promotion decision.

## Recovery acceptance

- Main SHA unchanged.
- Existing branch and PR refs unchanged.
- Candidate's final head and all rollback actions traceable.
- No live side effects occurred.
- Independent reviewer confirms the candidate is safely quarantined or reverted.

Rollback is a planned procedure, not an action already executed.
