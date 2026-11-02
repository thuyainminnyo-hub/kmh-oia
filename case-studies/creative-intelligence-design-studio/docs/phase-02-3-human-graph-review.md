# Phase 02.3 — Human Graph Review & Controlled Promotion

**Review state:** Project owner confirmed HOLD / DO NOT PROMOTE on 2026-11-02; additional independent evidence is still required.  
**Source run:** [Graphify disposable run 41430984629](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41430984629).  
**Raw artifact:** [Artifact 13134475847](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41430984629/artifacts/13134475847).  
**Graphify:** v0.9.100, source commit `f5155badddaa3286c78a51653791131e9e2e4d29`.

## 1. Review input integrity

The raw `graph.json` was downloaded from the original workflow artifact and SHA-256 pinned before review.

- Raw graph SHA-256: `c5ad7ea7fdd6b6c65c81726a0aec51c5bead7a3cf29ff85a59051eb6bd95abeb`
- Nodes: 12
- Edges: 17
- Confidence: 16 EXTRACTED, 1 INFERRED, 0 AMBIGUOUS
- Source files: `src/contract_guard.py`, `src/outfit_flow.py`

The original graph is immutable evidence. Review does not rewrite or replace the raw artifact.

## 2. Source-level adjudication

The one inferred edge is:

- From: `select_outfit()`
- To: `DesignToken`
- Relation: `uses`
- Confidence: `INFERRED`
- Source: `src/outfit_flow.py:L6`
- Edge fingerprint: `f3f463148fad99ea22391ba177933acab4de6a5aefff01ddfe8c260275d9fde3`

The source code at line 6 is:

```python
def select_outfit(token: DesignToken) -> dict[str, str]:
```

The same source node, target node, source file and line also carry an explicit Graphify edge:

- Relation: `references`
- Context: `parameter_type`
- Confidence: `EXTRACTED`
- Source: `src/outfit_flow.py:L6`

This directly describes the parameter type, but it does not prove that the broader `uses` relation is redundant.

### Review recommendation

**HOLD — DO NOT PROMOTE**

The inferred `uses` edge has source corroboration but remains INFERRED. The pinned Graphify implementation creates `uses` edges during Python cross-file import resolution when an imported identifier is encountered within a local symbol's AST subtree. In this fixture, the edge anchor at L6 is the `DesignToken` type annotation; the function also checks and reads fields from the typed token at runtime. This supports a dependency, but does not independently settle the broader semantic meaning of `uses`.

**Project-owner decision: CONFIRMED HOLD — DO NOT PROMOTE.** Preserve the edge in the immutable raw graph and review ledger, keep it excluded from the EXTRACTED-only candidate, and gather additional evidence. It is not being declared a false positive.

## 3. Additional upstream and source evidence

At the exact pinned Graphify v0.9.100 source commit, `graphify/extractors/resolution.py` documents the Python cross-file import-resolution pass. It builds imported-name targets, walks identifiers within local class/function AST subtrees, and emits an INFERRED `uses` edge when the local symbol references an imported name. The source anchor records the actual identifier line. See [pinned upstream implementation, lines 3039–3218](https://github.com/Graphify-Labs/graphify/blob/f5155badddaa3286c78a51653791131e9e2e4d29/graphify/extractors/resolution.py#L3039-L3218).

Independent standard-library AST inspection corroborates:
- `outfit_flow.py:L3` imports `DesignToken` from `contract_guard`.
- `outfit_flow.py:L6` annotates `select_outfit(token: DesignToken)`.
- `outfit_flow.py:L8` passes `token` to `is_approved_token`.
- `outfit_flow.py:L10` reads `token.token_name`.
- `contract_guard.py:L7-L9` defines `DesignToken` and its `token_name` / `approved` fields.

The new `scripts/validate_inferred_edge_evidence.py` checks the current synthetic fixture using Python's standard-library AST. Actual GitHub Actions run [41438633133](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41438633133) passed the check with zero errors and uploaded [source-evidence artifact 13136524575](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41438633133/artifacts/13136524575). A PASS means the source structure is present; it does **not** change the edge's confidence or authorize promotion.

The precise unresolved question is semantic scope: whether this inferred `uses` relation should stand as a trusted, broader dependency fact in addition to the EXTRACTED type-reference edge. No further Graphify extraction is performed under the consumed one-run approval. A future controlled comparison would require a separate approval and fixtures that distinguish type-annotation-only references from body-level imported-object use.

## 4. Controlled candidate

The deterministic review tool `scripts/review_graphify_edges.py` creates a new candidate view without modifying raw graph data.

| Metric | Raw graph | Extracted-only candidate |
|---|---:|---:|
| Nodes | 12 | 12 |
| Edges | 17 | 16 |
| EXTRACTED | 16 | 16 |
| INFERRED | 1 | 0 |
| AMBIGUOUS | 0 | 0 |
| Cross-file edges | 6 | 5 |

- Candidate graph SHA-256: `c2053e83445e8b4c94d5c29a9a3ef816ccf15561c5a76cd8139e2412584123c1`
- Repository artifact: [extracted-only-candidate-graph.json](../artifacts/phase-02-3/extracted-only-candidate-graph.json)
- Machine-readable promotion report: [promotion-report.json](../artifacts/phase-02-3/promotion-report.json)
- Raw graph remains unchanged.
- External `dataclasses` node remains explicitly marked as an external reference.
- The candidate status is `CANDIDATE_ONLY_HOLD_CONFIRMED_NOT_PROMOTED`; it is not a production or main-branch promotion.

## 4. Reproducibility and guard tests

The review tool requires the exact raw graph SHA, validates the edge fingerprint and decision identity, requires an explicit decision for every non-EXTRACTED edge, rejects duplicate edge identities, and refuses to promote inferred edges. Eight unit tests cover those controls.

Latest verified PR-head CI on `a3c2bb6fa59441ae98db69ddb924fa7420443a0b`:

- Creative Studio QA: **50/50 tests PASS**, including live held-edge source corroboration and report artifact upload — [run 41438633133](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41438633133).
- KMH OIA Tests: **462/462 PASS** and performance baseline — [run 41438640569](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41438640569).
- KMH OIA Validation: **SUCCESS**, including repository validation and deployment evidence bundle — [run 41438640593](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41438640593).
- Graphify dependency audit: **SUCCESS** — [run 41438640641](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41438640641).

The owner-confirmed HOLD is encoded in the machine-readable decision manifest and promotion report.

## 5. Gate status

- G2 — Disposable extraction: PASS.
- G3 — Source traceability: PASS.
- G4 — Assistant-assisted edge review recommendation: COMPLETE.
- G4 — Project-owner HOLD disposition: CONFIRMED; inferred edge remains OPEN for additional evidence.
- G6 — Extracted-only candidate generation: PASS, candidate only.
- Production promotion / runtime integration: NOT AUTHORIZED.

The next work is evidence collection and independent semantic review. The owner has already confirmed HOLD. No Graphify re-extraction, package installation, global graph update, raw-graph rewrite or production change is authorized by this decision.
