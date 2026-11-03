# Phase 823 — Cognitive Learning Strategy Engine

## Scope
Sandbox-only, deterministic strategy guidance for EduAutomate. This module translates learning-science findings into educator-controlled practice options. It does not infer brain activity, hormones, emotions, diagnoses, intelligence, or learner traits.

## Evidence basis
Ruitenburg et al. (2026), *Educational Psychology Review*, meta-analysis of 53 studies and 7,303 learners in authentic primary/secondary classrooms:
- Retrieval practice: Hedges' g = 0.37 (95% CI 0.18–0.56).
- Distributed practice: g = 0.20 (95% CI 0.03–0.36).
- Interleaved practice: g = 0.40 (95% CI 0.10–0.71).
The authors report meaningful moderators and residual heterogeneity. These are group-level averages, not predicted gains for an individual learner. Interleaving feedback-timing findings are moderator observations and should not be converted into a universal delayed-feedback rule.

Source: https://doi.org/10.1007/s10648-026-10225-5

## Implementation
- Typed registry for retrieval, distributed, interleaved, elaboration, and dual-coding guidance.
- Educator-authored revision intervals are validated, not algorithmically optimized.
- Feedback timing is explicit and educator-selected.
- No student profile, emotion inference, demographic data, or automated high-stakes decision.
- Guidance includes boundary conditions to avoid one-size-fits-all recommendations.

## Validation
Run:
- python -m compileall -q src tests
- python -m unittest discover -s tests -v
- python scripts/deployment_preflight.py
- python -m scripts.production_readiness_snapshot

## Acceptance and release gates
1. Unit tests and compile check pass on the PR head SHA.
2. Existing repository validation workflow succeeds.
3. Independent review confirms evidence wording and privacy scope.
4. EduAutomate API contract and sandbox integration tests are supplied and pass before connecting to live learner records.
5. Rollback/recovery rehearsal is evidenced.
6. Production deployment remains HOLD until a separate release-specific approval.

## Rollback
No migration or production service changes are included. If validation fails, leave the branch unmerged and retain the previous base branch/main unchanged. Remove or abandon the feature branch after recording the failure evidence; do not attempt a production rollback for code that was never deployed.
