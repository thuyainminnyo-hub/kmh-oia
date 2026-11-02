# Phase 02.6 — Cross-file Canonical Identity & Semantic Relationship Validation

**Status:** Implementation committed; PR-head CI verification pending.  
**G4:** Owner-confirmed HOLD remains unchanged.  
**Graphify execution:** Not performed.  
**Production promotion:** Not authorized.

## 1. Upstream verification and corrected risk assessment

The original upstream Issue [#1186](https://github.com/Graphify-Labs/graphify/issues/1186) was reported against Graphify v0.8.35 and remains open. Its maintainer comments state that full-path IDs and earlier language-specific fixes address much of the ghost-duplicate problem while leaving other language/cross-file inheritance cases open.

The exact pinned v0.9.100 source commit `f5155badddaa3286c78a51653791131e9e2e4d29` contains relevant Python changes:
- `graphify/extractors/resolution.py` has a type-reference repointing pass for `references`, `inherits`, `implements`, and `extends`, binding sourceless stubs to exact imported target definitions.
- `tests/test_extract.py::test_cross_file_type_annotation_refs_resolve_to_single_node` verifies one canonical node for cross-file parameter/return type references.
- `tests/test_extract.py::test_3252_inheritance_repoints_inherits_edge` verifies imported class inheritance targets the canonical definition and leaves no sourceless stubs.
- `graphify/ids.py` centralizes casefold/NFKC ID normalization and declaration-collision handling.

These are real pinned-source and test artifacts, not a claim that every cross-file scenario or every language is fixed. Issue #1186 remains a residual upstream risk outside the exact covered cases.

References:
- [Pinned v0.9.100 resolver](https://github.com/Graphify-Labs/graphify/blob/f5155badddaa3286c78a51653791131e9e2e4d29/graphify/extractors/resolution.py#L3190-L3250)
- [Pinned Python extraction tests](https://github.com/Graphify-Labs/graphify/blob/f5155badddaa3286c78a51653791131e9e2e4d29/tests/test_extract.py#L150-L180)
- [Pinned inheritance regression test](https://github.com/Graphify-Labs/graphify/blob/f5155badddaa3286c78a51653791131e9e2e4d29/tests/test_extract.py#L6190-L6225)
- [Pinned ID normalization](https://github.com/Graphify-Labs/graphify/blob/f5155badddaa3286c78a51653791131e9e2e4d29/graphify/ids.py)

## 2. Phase 02.6 independent validator

Added `scripts/validate_canonical_semantics.py`. It uses Python's standard-library AST to resolve only project-internal imports inside the allowlisted two-file synthetic fixture. It then checks:
- imported target name maps to exactly one source declaration in the imported file;
- the graph has exactly one canonical node at the target declaration file and line;
- local source function/class maps to exactly one graph source node;
- type annotations map to `references/EXTRACTED` with the expected parameter/return/type context;
- imported calls map to `calls/EXTRACTED`;
- imported class bases map to `inherits/EXTRACTED`;
- raw and candidate graphs both retain each required EXTRACTED semantic relationship;
- the G4 `uses/INFERRED` edge remains owner-confirmed HOLD in raw and absent from candidate;
- non-unique imported declarations fail closed rather than resolving by first match.

The validator does not execute Graphify and is not a reproduction of Graphify's Tree-sitter resolver. It independently checks whether the expected source identity and semantic relation in the existing graph agree.

Python AST represents parameter annotations, return annotations, calls and class bases as distinct nodes/fields. See [Python 3.12 AST documentation](https://docs.python.org/3.12/library/ast.html).

## 3. Current pilot semantic expectations

| Source evidence | Expected edge | Canonical target |
|---|---|---|
| `select_outfit(token: DesignToken)` at L6 | `references / EXTRACTED / parameter_type` | `src_contract_guard_designtoken` at L7 |
| `is_approved_token(token)` at L8 | `calls / EXTRACTED / call` | `src_contract_guard_is_approved_token` at L12 |
| Graphify's additional `uses` at L6 | `INFERRED / HOLD_NOT_PROMOTED` | Same DesignToken node; raw only |

The runtime field read `token.token_name` is not treated as a second reference to the imported identifier `DesignToken`. The relation `uses` is not upgraded merely because its target is canonical.

## 4. Regression tests

Nine regression tests cover:
1. Aliased imported type, call target, and class inheritance all resolve to canonical nodes.
2. A type-reference edge aimed at a ghost ID fails.
3. Missing canonical target fails.
4. Duplicate canonical target nodes fail.
5. Missing runtime call edge fails.
6. Wrong inheritance target fails.
7. Held INFERRED edge leaking into the candidate fails.
8. Owner HOLD changed from CONFIRMED fails.
9. Duplicate imported declarations fail closed.

## 5. Version and governance boundary

The Phase 02.5 raw graph and candidate hashes remain the immutable input:
- Raw: `c5ad7ea7fdd6b6c65c81726a0aec51c5bead7a3cf29ff85a59051eb6bd95abeb`.
- Candidate: `c2053e83445e8b4c94d5c29a9a3ef816ccf15561c5a76cd8139e2412584123c1`.
- Graphify: v0.9.100 / `f5155badddaa3286c78a51653791131e9e2e4d29`.

No raw graph, candidate, decision manifest, or Graphify pin is modified. The one-run Graphify extraction approval remains consumed; no extraction is performed in Phase 02.6.

## 6. Gate status

- G4 — `uses/INFERRED`: owner-confirmed HOLD, unchanged.
- G9 — canonical imported target identity: IMPLEMENTED; CI verification pending.
- G9 — type references / calls / inheritance semantic links: IMPLEMENTED; CI verification pending.
- G9 — duplicate/ambiguous import fail-closed guard: IMPLEMENTED; CI verification pending.
- Raw/candidate mutation: NO.
- Graphify execution: NO.
- Production promotion / OIA runtime integration: NOT AUTHORIZED.
