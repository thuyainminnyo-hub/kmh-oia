# KMH OIA × EduAutomate — Human Intelligence Engine 7.7

## Change record
- Target: Human Intelligence Engine 7.7 — EduAutomate Integration
- Authorization: Project Owner approval recorded in conversation on 2026-11-03
- Branch: feat/human-intelligence-engine-7.7-eduautomate
- Base branch: main; observed base commit d96fc7fdcbbed8556da6c4fe499e71553578163e
- Deployment: not performed; production release remains gated

## Scope
Add deterministic, privacy-minimizing learning-evidence primitives to the existing Python runtime. This is an integration foundation, not a deployed EduAutomate service or psychological assessment product.

Included:
- Typed evidence contract using pseudonymous learner and task references.
- Separate task-performance, independent-learning, and delayed-retention scores.
- Observable planning, verification, and reflection signals.
- Conservative status distinguishing missing evidence from observed absence.
- Human escalation for high-risk tasks.
- Standard-library unit tests.

Excluded:
- Names, contact details, health data, demographic profiling, emotion inference, diagnosis, or automated learner ranking.
- Automated grading or consequential student decisions.
- External provider calls, credentials, database migration, UI changes, and production deployment.
- Any modification to main or existing production services.

## Evidence semantics
- None means not measured; never convert it into a negative result.
- False or zero means an explicit observation was recorded.
- Engagement status is a workflow aid, not a claim about a learner's internal mental state.
- Task performance and independent learning remain separate metrics.
- High-risk tasks require qualified human review.

## Validation
Run from repository root:
- python -m compileall -q src tests
- python -m unittest discover -s tests -v
- python scripts/deployment_preflight.py
- python -m scripts.production_readiness_snapshot

The existing validation workflow runs tests, compilation, deployment preflight, performance evidence, and readiness snapshot generation. A HOLD readiness result is a release blocker, not a CI malfunction.

## QA and rollback
1. Review the branch diff and ensure only scoped files changed.
2. Require CI to pass on the pull request.
3. Review test output and retained artifacts against the exact head commit.
4. Perform independent code and privacy review.
5. Keep the change in a draft pull request until all gates are satisfied.
6. If validation fails, do not merge; close or abandon the branch and retain the last known-good main commit.
7. Production release requires a separately verified environment, backup/recovery evidence, rollback owner, and release-specific approval.

## Release decision
HOLD until CI, independent QA, deployment environment, operational rollback, and production readiness evidence are verified. Owner authorization of the target does not waive these gates.
