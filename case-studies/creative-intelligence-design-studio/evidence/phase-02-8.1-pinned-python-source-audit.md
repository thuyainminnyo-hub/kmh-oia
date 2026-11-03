# Phase 02.8.1 — Pinned Python Source Audit

This stacked change supplements the Phase 02.8 research draft with the exact Python cross-file type-rewiring evidence found in Graphify v0.9.100.

- Pinned upstream release: `0.9.100`, commit `f5155badddaa3286c78a51653791131e9e2e4d29`
- Python type fix: `b2825e05a5655be1187250a6acb69b83027acd8a` (commit subject references #3252)
- GitHub compare confirms the fix commit is an ancestor of the pinned release commit.
- Implementation: `graphify/extractors/resolution.py`, Python import facts and cross-file import target repointing.
- Relations repointed: `references`, `inherits`, `implements`, `extends`.
- Regression inventory: 12 upstream cases mapped in `contracts/phase-02-8-upstream-python-audit.json`.

## Important scope distinction

The v0.9.100 release notes advertise the Java/Kotlin cross-file fix, not the Python #3252 change. The Python fix is nevertheless present in the pinned source ancestry and direct Python tests. Therefore the release-note claim and source-level claim must remain separate.

## Remaining risks

- Issue #1186's original 891-file corpus has not been reproduced on v0.9.100.
- Issue #3252 remains open in GitHub even though its exact fix commit is in the pinned ancestry.
- Same imported symbol as both parameter and return on one signature line is not explicitly covered by the upstream return-context test.
- The inherited-method resolver stops at multiple-base classes because cross-file MRO ordering is not modelled.
- Synthetic AST shape tests prove Python AST fields, not Graphify emitted edges.

## Governance

No Graphify extraction ran in Phase 02.8.1. Raw/candidate graphs remain untouched. G4 Owner HOLD remains. INFERRED/AMBIGUOUS promotion, production promotion, and OIA runtime integration remain unauthorized.
