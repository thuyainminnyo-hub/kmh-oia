# Phase 02.4 — Independent Semantic Evidence & Candidate Versioning

**Status:** Static AST context matrix implemented; awaiting PR-head CI verification.  
**Owner decision:** G4 HOLD / DO NOT PROMOTE remains confirmed.  
**Production:** Not authorized.  
**Graphify extraction:** Not performed in this phase.

## 1. Why this phase exists

The held raw edge is `select_outfit()` → `DesignToken`, relation `uses`, confidence `INFERRED`, anchored at `src/outfit_flow.py:L6`.

The pinned Graphify v0.9.100 implementation in `graphify/extractors/resolution.py` first maps imported names to target nodes, then walks identifiers inside each local class/function AST subtree. When the local symbol references an imported name, it emits an INFERRED `uses` edge and records the source line. The upstream comments describe this as a reference inside the local symbol; the implementation does not apply a separate semantic filter that distinguishes type-annotation identifiers from executable-body identifiers. See [pinned v0.9.100 resolver source](https://github.com/Graphify-Labs/graphify/blob/f5155badddaa3286c78a51653791131e9e2e4d29/graphify/extractors/resolution.py#L3039-L3218).

The current synthetic fixture imports `DesignToken` at L3 and references the identifier in the `select_outfit(token: DesignToken)` parameter annotation at L6. Later, the function reads `token.token_name`, but the imported symbol name `DesignToken` does not reappear in that runtime attribute access. These are different AST references:
- `DesignToken` at L6 is a type-annotation reference to the imported class.
- `token` at L8/L10 is the runtime parameter value used by the function.
- Runtime field access on `token` is not itself a second identifier reference to the imported name `DesignToken`.

This distinction is the exact reason the edge stays under owner-confirmed HOLD.

## 2. Independent AST context matrix

Added `scripts/analyze_inferred_edge_context.py`. It uses Python's standard-library AST only and classifies occurrences of one imported symbol within one local function/class as:
- `TYPE_ANNOTATION`
- `RUNTIME_CALL`
- `RUNTIME_BODY_REFERENCE`

The tests cover:
1. Annotation-only reference.
2. Runtime constructor/call reference.
3. Both annotation and runtime call.
4. Imported but unused symbol.
5. Type annotation plus runtime field access through the typed parameter (the pilot's shape).
6. Aliased import.
7. Return annotation.
8. Incorrect import module rejection.

**Interpretation boundary:** This is an independent source-context model. It is not Graphify's Tree-sitter execution and does not claim to reproduce Graphify output. It tells reviewers what kind of source reference exists before any new Graphify run is considered.

## 3. Test matrix and expected source evidence

| Fixture shape | Expected source classification | What it proves |
|---|---|---|
| `def f(x: DesignToken)` | TYPE_ANNOTATION | Imported name occurs in a signature type |
| `return DesignToken()` | RUNTIME_CALL | Imported class name is called in executable code |
| Annotation + constructor | Both categories | Both signature and body references exist |
| Import with no reference | No matching site | Import alone does not demonstrate a local symbol use |
| `def f(x: DesignToken): return x.token_name` | TYPE_ANNOTATION only for `DesignToken` | Runtime use of `x` is not a body reference to the imported class name |

The classification does not assign trust to any Graphify edge. Confidence remains `INFERRED` where Graphify emitted the edge.

## 4. Candidate and raw evidence versioning

No graph file is rewritten in Phase 02.4.

| Evidence | Identity | State |
|---|---|---|
| Raw graph v0 | SHA-256 `c5ad7ea7fdd6b6c65c81726a0aec51c5bead7a3cf29ff85a59051eb6bd95abeb` | Immutable |
| EXTRACTED-only candidate v1 | SHA-256 `c2053e83445e8b4c94d5c29a9a3ef816ccf15561c5a76cd8139e2412584123c1` | Separate, candidate only |
| Held `uses` edge | Fingerprint `f3f463148fad99ea22391ba177933acab4de6a5aefff01ddfe8c260275d9fde3` | `CONFIRMED_HOLD` |

The raw graph continues to contain 12 nodes / 17 edges (16 EXTRACTED, 1 INFERRED). The extracted-only candidate remains 12 nodes / 16 EXTRACTED edges. Neither hash should change as a result of this phase.

## 5. Evidence required before revisiting HOLD

A future controlled Graphify comparison should use separate, synthetic fixtures for:
- type-annotation-only imported symbol;
- executable constructor/call use;
- import present but unused.

This would test actual Graphify edge emission and source anchors, not just Python AST context. **That extraction needs a new explicit owner approval** because the earlier one-run disposable approval was consumed. No Graphify install, extraction, global graph merge, or OIA runtime integration is authorized by this phase.

## 6. Gate status

- G4 — Owner decision: CONFIRMED HOLD; DO NOT PROMOTE.
- G4 — Independent semantic evidence: OPEN until reviewers agree on the intended semantics of `uses`.
- G7 — AST context matrix: IMPLEMENTED; CI verification pending.
- Candidate versioning: PRESERVED; no graph hash changes expected.
- Production promotion / runtime integration: NOT AUTHORIZED.
