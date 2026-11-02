# Phase 01 Acceptance Gates

## Scope

Phase 01 proves that KMH has a coherent, machine-checkable Creative Studio design foundation. It does not prove that all external creative tools are installed or that a learner-facing website is ready.

| ID | Gate | Acceptance evidence | Current result |
|---|---|---|---|
| P1-01 | Design contract exists | `DESIGN.md` and JSON contract committed | PASS |
| P1-02 | Design contract validates | Validator reports required fields and contrast checks pass | Pending execution |
| P1-03 | Negative cases fail closed | Unit tests for missing token, low contrast, reduced motion and unknown token | Pending execution |
| P1-04 | Skills are scoped | Three local skill specifications; no external install | PASS — specification only |
| P1-05 | External intake is governed | Security policy, allowlist and human approval gates documented | PASS — documentation |
| P1-06 | OIA core remains unchanged | Diff contains only isolated case-study module and workflow | Pending PR diff review |
| P1-07 | CI verifies baseline | GitHub Actions unit tests and contract validation pass | Pending CI |

## Phase 02 entry criteria

Do not install or run Graphify/Designer Skills until:

1. Project owner approves the exact repository folders to index.
2. A secret/data exclusion list exists and is tested.
3. Third-party source, license, dependency and permission review is recorded.
4. A project-scoped installation is selected and pinned.
5. Output is reviewed against the design contract by a human.

## Promotion rule

Phase 01 may be marked complete only when local tests and CI pass. The Creative Studio must remain **Pilot / Not Production** until browser-based UX review, accessibility checks, real device testing, learner/privacy review, and a release decision are completed.
