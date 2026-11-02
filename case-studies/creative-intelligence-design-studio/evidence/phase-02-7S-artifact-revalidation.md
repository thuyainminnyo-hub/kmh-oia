# Phase 02.7-S — Artifact-only Validator Revalidation

Date: 2026-11-02  
Branch: `phase-02-7S-validator-revalidation-20261102`

## Execution boundary

This phase did **not** install or run Graphify and did not perform a new extraction. It downloaded and revalidated the immutable artifact from the single authorized Phase 02.7-R run `41475845115`.

## Changes

1. Inheritance matching now checks canonical source/target IDs, relation, confidence, source file and source line without requiring a context field that Graphify did not emit for `inherits`.
2. Same-line parameter and return annotations are handled as a coalesced edge only when the AST proves that the same imported name is used in both positions on the same function-signature line.
3. The validator records `SIGNATURE_ANNOTATION_EDGE_COALESCED` warnings and explicitly states that the raw edge's `parameter_type` context does not independently prove return-specific context.
4. Candidate matching uses the observed edge context while retaining the AST semantic context in the evidence record.
5. The summary status distinguishes `PASS_WITH_WARNINGS` from an unqualified `PASS`.

## CI evidence

- Workflow: KMH Phase 02.7-S Artifact Revalidation
- Run: [41477405458](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41477405458)
- Conclusion: SUCCESS
- Archived extraction run: [41475845115](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41475845115)
- Focused Phase 02.7 regression tests: PASS
- Archived artifact raw and candidate hash comparison: PASS
- Graphify execution count during Phase 02.7-S: 0

## Revalidation results

- Status: `PASS_WITH_WARNINGS`
- Errors: 0
- Warnings: 2
- Canonical semantic links evaluated: 21
- Candidate semantic links verified: 21
- Raw graph: 41 nodes, 83 edges (73 EXTRACTED, 10 INFERRED)
- Extracted-only candidate: 41 nodes, 73 EXTRACTED edges
- Candidate non-EXTRACTED edges: none

The two warnings are return-annotation context coalescing for `Widget` in package alpha and package beta. Each has one matching EXTRACTED canonical edge, but the extractor records that edge as `parameter_type`; therefore return-specific context remains only partially evidenced.

## Immutable evidence

- Raw graph SHA-256: `c91bc6919ebf5dcd6740239f017e4c8fc58c155e1b5738febf09029dfb335168`
- Candidate graph SHA-256: `c35d5f61ca4ba4fec1b54967c623eeeb675e09e0e6324c4bd7d1140089a8f95c`
- Revalidation artifact: `kmh-phase-02-7S-revalidation-41477405458`
- Artifact SHA-256: `a5e3717c2aa976b03a185688d622407b5475a44d5a8b1bd270cfb815cdc7829d`
- Artifact retention expiry: 2026-11-16T16:01:53Z

The revalidated raw and candidate hashes exactly match the original Phase 02.7-R archived validation summary. Raw graph was not mutated. Candidate remains separate and EXTRACTED-only.

## Governance decision

- G4 Owner HOLD: PRESERVED
- INFERRED edges promoted: NO
- AMBIGUOUS edges promoted: NO
- Production promotion: NOT AUTHORIZED
- OIA runtime integration: NOT AUTHORIZED
- Additional Graphify extraction: NOT performed; the Phase 02.7-R one-run approval remains consumed.

**Decision:** Validator identity/relationship checks now pass against the archived graph with two explicit semantic-context warnings. The canonical endpoints are verified; return-specific annotation context remains partially evidenced. This is not a production-promotion decision.
