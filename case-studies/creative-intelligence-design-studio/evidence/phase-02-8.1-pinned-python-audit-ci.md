# Phase 02.8.1 — Pinned Python Source Audit CI Evidence

Date: 2026-11-03

## CI result

- Workflow: KMH Phase 02.8.1 Pinned Python Audit CI
- Run: [41553289250](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41553289250)
- Conclusion: SUCCESS
- Job: `pinned-upstream-contract`
- JSON audit contract validation: PASS
- Pinned upstream audit contract tests: 6/6 PASS
- Phase 02.8 research contract tests: 6/6 PASS
- Synthetic Python AST fixture tests: 12/12 PASS
- `git diff --check`: PASS

## Scope statement

This run validates the pinned-source audit record and KMH synthetic AST/contract tests only. It did **not** install Graphify, execute Graphify, produce a new extraction, or compare new Graphify output.

## Upstream evidence classification

- Graphify v0.9.100 pinned commit: `f5155badddaa3286c78a51653791131e9e2e4d29`
- Python cross-file type-reference fix commit: `b2825e05a5655be1187250a6acb69b83027acd8a`
- GitHub compare confirmed the Python fix commit is an ancestor of the pinned release commit.
- Pinned source contains Python import resolution and sourceless target repointing for `references`, `inherits`, `implements`, and `extends`.
- Upstream direct regression inventory: 12 test scenarios found and mapped.
- Issue #1186 remains OPEN; its original 891-file corpus has not been reproduced on v0.9.100.
- Issue #3252 remains OPEN although its fix commit is present in the pinned release ancestry.

## Remaining explicit limitations

1. Same imported type used for both parameter and return annotation on one signature line is not explicitly covered by the located upstream annotation regression test; KMH Phase 02.7's two return-context warnings remain.
2. Cross-file inherited-method lookup explicitly stops for multiple-base classes because cross-file MRO ordering is not modelled. This limitation is distinct from the base-edge repoint mechanism.
3. Annotated assignments, nested lexical scopes, string forward references, and star-import symbol resolution still require KMH-specific Graphify-output differential evidence; AST-only tests do not prove emitted graph relationships.
4. No run against the original Issue #1186 corpus was performed.

## Governance

- Graphify executions in Phase 02.8/02.8.1: 0
- Raw graph mutation: false
- Candidate graph mutation: false
- INFERRED/AMBIGUOUS promotion: not authorized
- G4 Owner HOLD: preserved
- Production promotion: NOT AUTHORIZED
- OIA runtime integration: NOT AUTHORIZED
- A fresh Owner Approval is required before any new Graphify extraction.

Stacked draft PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/191
