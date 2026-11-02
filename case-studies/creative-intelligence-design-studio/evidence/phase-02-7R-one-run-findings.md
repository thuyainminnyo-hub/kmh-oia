# Phase 02.7-R — One-run extraction findings

Date: 2026-11-02  
Branch: `phase-02-7-recovery-once-20261102-r1`  
Approval: `KMH-CREATIVE-GRAPHIFY-PHASE-02-7R-2026-11-02-RUN-01`

## Execution evidence

- GitHub Actions run: [41475845115](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41475845115)
- Run attempt: 1 (the only authorized attempt)
- Graphify: `graphifyy==0.9.100`
- Graphify source commit: `f5155badddaa3286c78a51653791131e9e2e4d29`
- uv: `0.13.6`; frozen lock blob: `1fd2344a28be6b14c4f6f41c4901c70cadc2be0e`
- Approved scan corpus: exactly 10 synthetic Python files plus `.graphifyignore`
- Approval/base-SHA/no-prior-run guards: PASS
- Source pin verification: PASS
- Read-only scan snapshot: PASS
- Frozen runtime installation: PASS
- One code-only extraction without model credentials: PASS
- Independent graph validator: FAIL (7 strict-context mismatches)
- Raw graph and sanitized validation evidence artifact: uploaded successfully
- Temporary workspace cleanup: PASS

Artifact: `kmh-graphify-phase-02-7-one-run-41475845115`  
Artifact SHA-256: `1f43d0ee2ee0156ae92fc759c89041750fd56377e7e395155cc43a2b76b55e3d`  
Retention expiry: 2026-11-16T15:52:40Z

## Graph output

- Nodes: 41
- Edges: 83 (73 EXTRACTED, 10 INFERRED)
- Cross-file edges: 49
- Import resolutions: 15
- Synthetic coverage cases: 13/13 PASS
- Canonical semantic links evaluated: 21
- Candidate links admitted: 14
- Candidate graph: 41 nodes, 73 EXTRACTED edges only
- Candidate contains non-EXTRACTED edges: false
- Unanchored external nodes: 1

## QA finding

The validator reported seven `CANONICAL_SEMANTIC_EDGE_NOT_UNIQUE` errors:

- Five class-inheritance edges have exact source node ID, target canonical node ID, relation, source file, source line and EXTRACTED confidence in the raw graph, but Graphify does not attach a `context` field to those `inherits` edges. The validator currently requires context `base`.
- Two return-annotation edges have the expected canonical source/target IDs, relation, source file, source line and EXTRACTED confidence, but Graphify emits context `parameter_type` while the synthetic AST validator labels the context `return_type`.

An independent comparison of the seven failed records against the raw graph found exactly one matching EXTRACTED edge for each when the strict context equality is omitted. This indicates a validator/normalization contract mismatch, not evidence that the canonical node links are absent. It must be treated as a compatibility finding, not silently waived.

## Governance

- Raw graph mutation: false
- Candidate is separate: true
- INFERRED promotion: false
- AMBIGUOUS promotion: false
- Model credentials: absent
- OIA runtime integration: NOT AUTHORIZED
- Production promotion: NOT AUTHORIZED
- G4 Owner HOLD: PRESERVED
- Rerun: NOT ALLOWED under this approval

## Decision

**Phase 02.7-R extraction executed once; independent QA remains HOLD/FAIL pending a separately reviewed validator-contract correction.**

Do not rerun Graphify under this approval. Do not promote the candidate or alter the Phase 02.5 raw/candidate baselines. Any additional extraction requires a new owner approval and a new isolated run scope.
