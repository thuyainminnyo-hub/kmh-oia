# AEE-WIRE-04 — Appendix A.4 Reference Receipt Hash Vectors

**Status:** CODED / awaiting exact-head CI. This is a bounded reference-vector test addition, not full AEE conformance.

## Locked input source
The vectors are transcribed from the AEE -02 Appendix A.4 diagnostic examples and the accompanying deterministic vector generator. The four receipt records are task_start (seq 0), inference (seq 1), tool_call/confirm (seq 2), and allow outcome (seq 3).

## Implemented checks
- Recompute all four SHA-256 record hashes from deterministic CBOR maps.
- Verify the complete four-record sequence and predecessor-hash chain.
- Assert that receipt key 15 is included in the seq-2 record hash. The published vector represents this value as a byte string containing the encoded COSE_Sign1 object.
- Preserve the expected hash values as fixed test constants.

## Explicit limitations
- The key-15 COSE_Sign1 object is treated as opaque encoded bytes for record hashing. This test does **not** parse or cryptographically verify the COSE_Sign1 signature.
- The full COSE signed-statement wrapper, credential chain, CDDL validation, JCS, epoch/Merkle proofs, SCITT, and production evidence verification remain out of scope.
- These tests establish matching of the four published receipt record-hash vectors only. They do not establish semantic correctness, signer authority, event completeness, or complete AEE -02 conformance.
- The vector generator's comments refer to draft -01 while the profile lock targets -02; maintainers must confirm the published Appendix A.4 vectors remain unchanged in the locked -02 text before treating this fixture set as normative for later revisions.

## Verification gate
Require GitHub Actions on the exact branch head, inspect test output for the three reference-vector tests, and retain release decision HOLD until independent protocol/security review and all excluded conformance work are complete.
