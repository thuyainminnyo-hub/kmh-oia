# Phase 02.8 — Semantic Context Fidelity & Upstream Compatibility Research

Date: 2026-11-02  
Branch: `phase-02-8-semantic-context-research-20261102`  
Status: DESIGN / RESEARCH ONLY

## Executive finding

The upstream Graphify v0.9.100 release must not be represented as a blanket fix for Python cross-file canonical identity or inheritance. Its published release notes explicitly describe cross-file import, `extends`/`implements`, and member-call resolution for the JVM Java/Kotlin extractors, alongside a separate case-sensitive ID collision fix. They do not announce the corresponding Python fix.

Pinned release:
- Version: `0.9.100`
- Commit: `f5155badddaa3286c78a51653791131e9e2e4d29`
- Published: 2026-11-01
- Upstream release notes: https://github.com/Graphify-Labs/graphify/releases/tag/v0.9.100

## Issue #1186 — careful interpretation

The upstream issue is titled “AST extractor misses cross-file inheritance and produces ghost-duplicate nodes for cross-file type references.” The issue reports Graphify 0.8.35, was opened 2026-06-07, and was last updated 2026-06-28. The current repository API state observed during this research is OPEN.

Issue: https://github.com/Graphify-Labs/graphify/issues/1186

An OPEN issue is not, by itself, proof that the bug remains in every later version. Conversely, a later release note for Java/Kotlin is not proof that Python was fixed. Therefore Phase 02.8 retains Python compatibility as an unverified risk until pinned-source inspection and our synthetic regression matrix establish the exact behavior.

## Additional upstream signal

The v0.9.100 release page includes Java/Kotlin-specific cross-file resolution work. A separate issue #4874 describes Java/Kotlin import resolution and affected-graph omissions in earlier versions. These are JVM-specific signals and must not be generalized to Python.

- Release: https://github.com/Graphify-Labs/graphify/releases/tag/v0.9.100
- Issue #4874: https://github.com/Graphify-Labs/graphify/issues/4874

## Phase 02.7-S carry-forward

The artifact-only revalidation workflow completed successfully:
- CI run: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41477405458
- Result: PASS_WITH_WARNINGS
- Canonical semantic links: 21 evaluated / 21 candidate-verified
- Warnings: 2 coalesced return-annotation contexts
- Raw graph: 41 nodes / 83 edges (73 EXTRACTED, 10 INFERRED)
- Candidate: 41 nodes / 73 EXTRACTED edges
- Raw and candidate SHA-256 values matched the Phase 02.7-R archive
- Graphify was not run during Phase 02.7-S

The two warnings remain important: a single `parameter_type` edge on a function-signature line does not independently encode both parameter and return annotation contexts.

## Phase 02.8 test design

A 12-case semantic-context matrix is committed at:
`contracts/phase-02-8-semantic-context-matrix.json`

It covers:
1. Parameter annotation
2. Return annotation on its own
3. Same-line parameter + return annotation coalescing
4. Annotated assignment
5. Multiple inheritance
6. Aliased imports
7. Same-name definitions across packages
8. Nested lexical scope
9. String/forward-reference annotations
10. Generic/nested annotations
11. Star imports
12. Ambiguous internal declarations

Each case must state expected AST context, expected relationship semantics, and a fail-closed rule where the binding is ambiguous. A separate synthetic Python fixture corpus and 12 AST-shape tests have now been added under `tests/fixtures/phase_02_8/` and `tests/test_phase_02_8_ast_fixtures.py`. These validate Python AST distinctions only; they do not claim that Graphify emits the corresponding graph edges.

## Acceptance gates

- Canonical targets must match source file, declaration kind, and definition line; name-only matches are insufficient.
- Parameter, return, and variable annotation contexts must be represented independently where source provenance permits.
- If the extractor coalesces contexts, the report must say so explicitly and must not claim independently verified return semantics.
- Multiple inheritance must verify each base separately.
- Same-named definitions in different packages must retain distinct canonical IDs.
- Nested scope references must not leak into sibling or outer scopes.
- String annotations and star imports must be explicitly classified; no speculative edge promotion.
- Candidate graph remains EXTRACTED-only; raw graph is immutable.
- INFERRED and AMBIGUOUS edges remain review-only.
- G4 Owner HOLD remains in force.
- No Graphify extraction, dependency installation, production promotion, or OIA runtime integration is authorized in this phase.

## CI and review evidence

- Phase 02.8 synthetic contract CI: [run 41484180105](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41484180105) — SUCCESS
- The six contract tests and JSON syntax check passed in run 41484180105.
- Added 12 AST fixture tests for parameter/return annotations, same-line annotations, variable annotations, multiple inheritance, aliases, duplicate names, nested scopes, string forward references, generics, star imports, and duplicate declarations. The updated CI will run both suites.
- Draft integration PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/190
- PR base: `phase-02-7S-validator-revalidation-20261102`
- PR status: OPEN / DRAFT / UNMERGED

## Decision

**Phase 02.8 research and test-design contract created.** This is not a Graphify compatibility PASS and not an extraction result. The next safe action is to implement the 12 synthetic AST fixtures and contract tests, run CI against those fixtures only, and inspect the pinned upstream Python implementation/tests separately. A new Graphify run requires fresh, explicit owner approval after the test-design gate is reviewed.
