# Phase 01 Acceptance Gates

## Scope

Phase 01 proves that KMH has a coherent, machine-checkable Creative Studio design foundation. It does not prove that all external creative tools are installed or that a learner-facing website is ready.

| ID | Gate | Acceptance evidence | Current result |
|---|---|---|---|
| P1-01 | Design contract exists | `DESIGN.md` and JSON contract committed | PASS |
| P1-02 | Design contract validates | Hosted validator reports required fields and contrast checks pass | PASS — GitHub Actions #15 |
| P1-03 | Negative cases fail closed | Six synthetic tests for baseline, low contrast, missing token, reduced motion, unknown token, and brand contrast | PASS — 6/6 in GitHub Actions #15 |
| P1-04 | Skills are scoped | Three local skill specifications; no external install or global activation | PASS — specification only |
| P1-05 | External intake is governed | Security policy, exclusions, and human approval gates documented | PASS — documentation |
| P1-06 | OIA core remains unchanged | Compare against main shows 15 added files only; no existing source files modified/deleted | PASS — branch comparison |
| P1-07 | CI verifies baseline | Validator, unit tests, and `git diff --check` all pass | PASS — GitHub Actions #15 |

## Verified execution reference

- Workflow: **KMH Creative Design Studio QA #15**
- Run ID: `41415815018`
- Commit: `f06a61c9e801fd3ce751328817df95ab5f81a81e`
- Result: **SUCCESS**
- Contract validation: PASS
- Unit tests: **6 passed, 0 failed**
- Diff whitespace check: PASS
- [GitHub Actions evidence](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41415815018)

Local workstation re-run is **NOT RUN** in this environment because outbound DNS access to GitHub was unavailable. The successful result above is from GitHub-hosted CI, not a local shell session.

## Phase 02 entry criteria

Do not install or run Graphify/Designer Skills until:

1. Project owner approves the exact repository folders to index.
2. A secret/data exclusion list exists and is tested.
3. Third-party source, license, dependency and permission review is recorded.
4. A project-scoped installation is selected and pinned.
5. Output is reviewed against the design contract by a human.

## Promotion rule

**Phase 01 foundation is CI-validated, but not yet formally closed.** Formal closure requires local reproduction where available and owner acceptance of the design contract and skill specifications. The Creative Studio must remain **Pilot / Not Production** until browser-based UX review, accessibility checks, real-device testing, learner/privacy review, and an explicit release decision are completed.
