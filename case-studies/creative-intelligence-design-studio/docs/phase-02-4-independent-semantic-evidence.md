# Phase 02.4 — Independent Semantic Evidence & Candidate Versioning

**Status:** Static AST context matrix implemented and CI-verified on PR head `61200d6a723ad5cd1dc88fbdaebf229e249a5e0f`.  
**Owner decision:** G4 HOLD / DO NOT PROMOTE remains confirmed.  
**Production:** Not authorized.  
**Graphify extraction:** Not performed in this phase.

## 1. Why this phase exists

The held raw edge is `select_outfit()` → `DesignToken`, relation `uses`, confidence `INFERRED`, anchored at `src/outfit_flow.py:L6`.

The pinned Graphify v0.9.100 implementation in `graphify/extractors/resolution.py` first maps imported names to target nodes, then walks identifiers inside each local class/function AST subtree. When the local symbol references an imported name, it emits an INFERRED `uses` edge and records the source line. The upstream comments describe this as a reference inside the local symbol; the implementation does not apply a separate semantic filter that distinguishes type-annotation identifiers from executable-body identifiers. See [pinned v0.9.100 resolver source](https://github.com/Graphify-Labs/graphify/blob/f5155badddaa3286c78a51653791131e9e2e4d29/graphify/extractors/resolution.py#L3039-L3218).

The current synthetic fixture imports `DesignToken` at L3 and references the identifier in the `select_outfit(token: DesignToken)` parameter annotation at L6. Later, the function reads `token.token_name`, but the imported symbol name `DesignToken` does not reappear in that runtime attribute access. The actual CI-generated context report records exactly one `TYPE_ANNOTATION` at L6 and zero runtime-call/body references to the imported name. See [CI artifact 13145371926](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41453288854/artifacts/13145371926). These are different AST references:
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

### Current pilot fixture classification

The same independent analyzer classifies the current `graphify-sandbox/src/outfit_flow.py` fixture as one `TYPE_ANNOTATION` reference at L6 and zero imported-name `RUNTIME_CALL` / `RUNTIME_BODY_REFERENCE` sites inside `select_outfit()`. The later `token.token_name` access is a runtime field access through the parameter, not a second reference to the imported identifier `DesignToken`.

This statement is source-context classification only; it does not re-run Graphify and it does not promote the held edge.

### Upstream residual risk

An open Graphify upstream issue, [#1186](https://github.com/Graphify-Labs/graphify/issues/1186), reports cross-file type-annotation and inheritance cases that in Graphify v0.8.35 produced downgraded `uses/INFERRED` edges and duplicate ghost nodes. This is older-version evidence, not proof that v0.9.100 has the same defect. Our two-file synthetic fixture currently resolves the `references/EXTRACTED` edge to the expected canonical DesignToken node, but one fixture does not clear the general risk.

Therefore Phase 02.4 records the issue as a residual compatibility risk. A separate new-owner-approved Graphify extraction would be needed to test a broader fixture covering imported parameter annotations, return annotations, class bases, and canonical node IDs. The consumed one-run approval is not reused.

## 3. Test matrix and expected source evidence

| Fixture shape | Expected source classification | What it proves |
|---|---|---|
| `def f(x: DesignToken)` | TYPE_ANNOTATION | Imported name occurs in a signature type |
| `return DesignToken()` | RUNTIME_CALL | Imported class name is called in executable code |
| Annotation + constructor | Both categories | Both signature and body references exist |
| Import with no reference | No matching site | Import alone does not demonstrate a local symbol use |
| `def f(x: DesignToken): return x.token_name` | TYPE_ANNOTATION only for `DesignToken` | Runtime use of `x` is not a body reference to the imported class name |

The classification does not assign trust to any Graphify edge. Confidence remains `INFERRED` where Graphify emitted the edge. Python's AST grammar represents function parameter annotations separately on `ast.arg.annotation` and return annotations on `FunctionDef.returns`, which is why this context distinction is technically testable without executing Graphify. See [Python 3.12 AST documentation](https://docs.python.org/3.12/library/ast.html).

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

## 6. CI evidence and gate status

Verified PR-head workflows on `cc64691fb750099a5b47f5d2f89a9c73c09f1186`:
- Creative Studio QA [run 41453693011](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41453693011): **58/58 tests PASS**; held-edge source corroboration and AST-context classification both PASS; two evidence artifacts uploaded.
- Held-edge source evidence [artifact 13145084217](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41453693011/artifacts/13145084217).
- Imported-symbol context evidence [artifact 13145199045](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41453693011/artifacts/13145199045).
- KMH OIA Tests [run 41453692965](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41453692965): **462/462 tests PASS** and performance baseline PASS.
- KMH OIA Validation [run 41453693026](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41453693026): SUCCESS, including deployment evidence bundle.
- Graphify runtime dependency audit [run 41453692956](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41453692956): SUCCESS.

- G4 — Owner decision: CONFIRMED HOLD; DO NOT PROMOTE.
- G4 — Independent semantic evidence: OPEN until reviewers agree on the intended semantics of `uses` and the residual cross-file type-resolution risk is tested.
- G7 — AST context matrix: IMPLEMENTED and CI-VERIFIED; source-context evidence only, not Graphify reproduction.
- Candidate versioning: PRESERVED; no graph hash changes expected.
- Production promotion / runtime integration: NOT AUTHORIZED.
