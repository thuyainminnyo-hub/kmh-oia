# Phase 02.3 — Human Graph Review & Controlled Promotion

**Review state:** Evidence-based recommendation prepared; project-owner confirmation pending.  
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

The same source node, target node, source file and line already carry an explicit Graphify edge:

- Relation: `references`
- Context: `parameter_type`
- Confidence: `EXTRACTED`
- Source: `src/outfit_flow.py:L6`
- Superseding edge fingerprint: `a2862edf8aad97705966889fc749500789b5abba3130914e08ed10bff636a455`

### Review recommendation

**HOLD — DO NOT PROMOTE**

The inferred `uses` edge is semantically compatible with the source, but is broader and redundant: the explicit `references / parameter_type` edge already records the type annotation precisely. This is **not** adjudicated as a proven false positive. Preserve it in the raw evidence and review ledger; exclude it from the extracted-only candidate.

This review is an assistant-assisted recommendation. It is not recorded as the project owner's final approval.

## 3. Controlled candidate

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
- The candidate status is `CANDIDATE_ONLY_OWNER_CONFIRMATION_PENDING`; it is not a production or main-branch promotion.

## 4. Reproducibility and guard tests

The review tool requires the exact raw graph SHA, validates the edge fingerprint and decision identity, requires an explicit decision for every non-EXTRACTED edge, rejects duplicate edge identities, and refuses to promote inferred edges. Eight unit tests cover those controls.

Local test result: **8/8 PASS**. The repository CI must independently pass on the updated PR head before the review candidate is accepted.

## 5. Gate status

- G2 — Disposable extraction: PASS.
- G3 — Source traceability: PASS.
- G4 — Assistant-assisted edge review recommendation: COMPLETE.
- G4 — Project-owner confirmation of the HOLD disposition: PENDING.
- G6 — Extracted-only candidate generation: PASS, candidate only.
- Production promotion / runtime integration: NOT AUTHORIZED.

The next authorized decision is for the project owner to confirm whether the single inferred edge should remain on HOLD. No Graphify re-extraction, package installation, global graph update or production change is required for that decision.
