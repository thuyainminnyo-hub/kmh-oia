# Phase 02.5 — Independent Graph Integrity & Versioned Evidence Comparison

**Status:** Validator and 11 regression tests implemented; real raw/candidate pair locally verified. PR CI verification follows.  
**Owner decision:** G4 `CONFIRMED_HOLD` — keep the `uses / INFERRED` edge under review; do not promote.  
**Graphify execution:** Not performed.  
**Production promotion:** Not authorized.

## 1. Immutable inputs

The validator reads the original raw graph from the exact disposable workflow artifact, rather than reconstructing or editing it. The workflow downloads artifact `kmh-graphify-disposable-pilot-41430984629` from run `41430984629` and reads its `graph.json`. The extracted-only candidate is read from the version-controlled Phase 02.3 candidate file.

The baseline is pinned to Graphify v0.9.100, source commit `f5155badddaa3286c78a51653791131e9e2e4d29`, the original artifact ID, and the two graph SHA-256 digests.

| Input | Identity | Status |
|---|---|---|
| Raw graph | 12 nodes / 17 edges; SHA-256 `c5ad7ea7fdd6b6c65c81726a0aec51c5bead7a3cf29ff85a59051eb6bd95abeb` | Immutable |
| EXTRACTED-only candidate | 12 nodes / 16 edges; SHA-256 `c2053e83445e8b4c94d5c29a9a3ef816ccf15561c5a76cd8139e2412584123c1` | Separate candidate |
| Graphify source | v0.9.100 / `f5155badddaa3286c78a51653791131e9e2e4d29` | Pinned |

## 2. Integrity checks

`scripts/validate_graph_pair.py` validates:
- Raw and candidate hashes against the owner decision manifest, Phase 02.3 promotion report, and versioned Phase 02.5 baseline.
- Unique node IDs and canonical source signatures.
- Node source anchors against the two allowlisted synthetic Python fixtures.
- Code node IDs/labels against actual class/function definitions at the claimed source line; rationale nodes against their source docstrings.
- External nodes as explicit external references, not ghost source nodes.
- Edge endpoint resolution, confidence values, source paths, line anchors, and duplicate edge identities.
- Exact node parity between raw graph and candidate.
- Exact candidate edge set equality with every EXTRACTED raw edge; no missing EXTRACTED edge and no INFERRED/AMBIGUOUS candidate edge.
- An explicit owner-confirmed HOLD decision for each non-EXTRACTED raw edge.
- Metrics and provenance against the versioned evidence baseline.

A source-backed isolated node is reported as a warning for review. Different relationships between the same source node, target node and line are recorded as a co-located relation group, not automatically labelled a duplicate.

## 3. Current graph comparison (local deterministic run)

The exact original `graph.json` was downloaded from workflow artifact 13134475847 and its SHA-256 matched the pinned raw digest. The extracted-only candidate was independently recreated from the raw bytes for local verification; its SHA-256 matched the committed candidate digest.

| Check | Raw graph | Candidate |
|---|---:|---:|
| Nodes | 12 | 12 |
| Edges | 17 | 16 |
| EXTRACTED | 16 | 16 |
| INFERRED | 1 | 0 |
| Duplicate node IDs | 0 | 0 |
| Duplicate canonical node signatures | 0 | 0 |
| Duplicate edge identities | 0 | 0 |
| Unresolved endpoints | 0 | 0 |
| Ghost-node indicators | 0 | 0 |
| Isolated source-backed nodes | 0 | 0 |
| Internal cross-file edges | 6 | 5 |

One explicitly external `dataclasses` node is retained as an external reference; it is not treated as an unanchored project ghost.

The same `select_outfit()` → `DesignToken` edge location contains two different relation labels: `references` and `uses`. The validator records this as a semantic review signal. It does not call the edges duplicates, remove either edge from raw evidence, or change the owner-confirmed HOLD.

## 4. Regression tests

Eleven tests cover:
1. Valid raw/candidate pair and external-reference handling.
2. Raw hash tampering.
3. Candidate hash tampering.
4. Rejecting an INFERRED edge in the candidate.
5. Rejecting omission of a raw EXTRACTED edge.
6. Duplicate node IDs.
7. Dangling edge endpoints.
8. Ghost symbol at a claimed source anchor.
9. Owner HOLD cannot be removed.
10. External references are not classified as ghosts.
11. Input graph objects are not mutated.

Local result: **11/11 PASS**. The actual graph-pair validator returned **PASS / zero errors** against the downloaded raw artifact, committed candidate, source fixtures, owner decision, promotion report, and baseline.

## 5. CI provenance

The Creative Studio workflow downloads the exact raw artifact from a previous workflow run. GitHub's `actions/download-artifact` supports cross-run downloads when supplied with a token and run ID; this workflow requests read-only `actions: read` permission. See [GitHub download-artifact documentation](https://github.com/actions/download-artifact#download-artifacts-from-other-workflow-runs-or-repositories) and [GitHub workflow artifact guidance](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts).

The comparison report is uploaded as a 14-day workflow artifact and includes:
- baseline identifier and version;
- raw and candidate SHA-256;
- node/edge and confidence counts;
- duplicate, endpoint, source-anchor and ghost-node checks;
- candidate-to-raw parity;
- owner HOLD and no-promotion state;
- GitHub commit, run ID and run attempt.

This is evidence provenance and hash pinning, not a signed build attestation. No new token-write permission, artifact attestation action, Graphify re-installation or extraction is introduced.

## 6. Gate status

- G4 — Owner HOLD: CONFIRMED; `uses / INFERRED` stays under review.
- G8 — Raw/candidate integrity comparison: IMPLEMENTED; local actual-pair PASS, CI verification pending.
- G8 — Canonical node/source identity: local PASS; CI verification pending.
- G8 — Versioned evidence baseline: CREATED.
- Raw graph / candidate mutation: NO.
- Graphify execution in Phase 02.5: NO.
- Production promotion / OIA runtime integration: NOT AUTHORIZED.

Further Graphify extraction still requires a new explicit owner approval because the previous one-run disposable approval has been consumed.
