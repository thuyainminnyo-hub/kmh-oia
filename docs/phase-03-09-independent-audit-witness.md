# Phase 03.09 — Independent Audit Witness & Signed Checkpoint Prototype

**Status:** Prototype implemented; five focused tests and 666 total tests passed on code/test commit. All four CI workflows, including Windows Preservation Gate A, passed on that exact code/test commit.
**Date:** 2026-11-10
**Branch:** `phase-02-71/midi-golden-fixtures`

## Research basis

- RFC 9162 defines Signed Tree Heads, Merkle inclusion proofs and consistency proofs. Consistency proofs demonstrate that a newer tree preserves all leaves in a previously witnessed tree. RFC 9162 also cautions that a log may show different inconsistent views to different clients; independent monitoring/witnesses remain necessary.
- Sigstore Rekor architecture describes transparency services as witnesses of events rather than trusted storage, and calls for independent witnesses in logically separate trust domains. Its documentation also emphasizes signed checkpoints, inclusion/consistency verification and offline verification.
- This KMH phase is inspired by those principles but is not an RFC 9162 implementation and is not Rekor-compatible.
- References:
  - https://www.rfc-editor.org/rfc/rfc9162.html
  - https://github.com/sigstore/architecture-docs/blob/main/rekor-spec.md
  - https://docs.sigstore.dev/about/security/
  - https://docs.sigstore.dev/logging/overview/

## Implementation

New module: `scripts/audit_witness.py`

Public functions:
- `create_signed_checkpoint()`: create an Ed25519-signed checkpoint binding log ID, tree size, root hash, timestamp and log signing-key ID.
- `verify_signed_checkpoint()`: validate checkpoint schema, fields and Ed25519 signature.
- `verify_witness_receipt()`: verify the independent witness's signed receipt.

Class: `IndependentAuditWitness`
- Stores accepted checkpoints in a separate SQLite database.
- Uses WAL, synchronous=FULL, explicit BEGIN IMMEDIATE transaction and append-only UPDATE/DELETE triggers.
- Pins checkpoint hash, log ID, tree size and root.
- Rejects tree-size rollback.
- Rejects same-size conflicting root (equivocation).
- Requires a caller-supplied consistency-proof verifier for every tree growth after the first checkpoint.
- Signs a witness receipt over witness ID/public key, log ID, tree size, checkpoint hash and witnessed time.
- Detects a concurrent witness update before commit.

New tests: `tests/test_audit_witness.py`
- signed checkpoint and receipt verification after database reopen;
- checkpoint tampering rejection;
- tree-size rollback and same-size equivocation rejection;
- tree-growth rejection without proof and with invalid verifier; acceptance only when the supplied verifier returns true;
- append-only witness storage triggers.

Commits:
- witness implementation: `aeef5bfb819928f2d6e85e25cfe2fcd53d7a96e4`
- witness tests: `543631b89744680419eb8ef217317e9602e20ae2`

## Exact code/test CI evidence

Commit `543631b89744680419eb8ef217317e9602e20ae2`:
- OIA Tests run `42738837102`: SUCCESS, 666 tests; all five witness tests passed.
- OIA Validation run `42738837358`: SUCCESS, including deployment evidence bundle.
- MIDI Fixture Integrity run `42738837111`: SUCCESS.
- Preservation Gate A run `42738837392`: SUCCESS, Linux and Windows.

## Important trust boundaries and limitations

- The `consistency_verifier` is an injected callback. The repository currently does not implement RFC 9162 Merkle tree construction, inclusion-proof verification, or the RFC 9162 consistency-proof algorithm. Passing a callback that returns true is not itself cryptographic proof. Do not connect production trust decisions until a reviewed RFC 9162 verifier is implemented and independently tested against published vectors.
- The log's Ed25519 key and witness's Ed25519 key must be held by different operators/systems. The code cannot enforce organizational or infrastructure separation.
- The witness stores its own database locally. A privileged witness DB owner can still replace the database or alter schema/triggers. External replication, signed checkpoint gossip, multiple independent witnesses, and disaster recovery are not implemented.
- The witness private key is injected by the caller; there is no KMS/HSM/Vault integration or key rotation workflow in this module.
- A signed checkpoint proves what the log key asserted, not that all users received the same view. Gossip and cross-witness comparison are future requirements.
- Checkpoint timestamps are signed but are not independently trusted timestamps. A trusted timestamp authority or independently monitored time source is not integrated.
- The current checkpoint schema is KMH-specific and not wire-compatible with RFC 9162 or Sigstore Rekor.
- No recovery mutation executor is enabled. PR #217 remains OPEN / DRAFT. No production-readiness claim.

## Next acceptance gates

1. Implement RFC 9162-compatible Merkle leaf/node hashing, tree-head serialization and inclusion-proof verification.
2. Implement RFC 9162 consistency-proof generation and verification in-house or use a well-reviewed compatible library; test against published vectors and adversarial cases.
3. Add two-or-more independent witnesses, checkpoint gossip and split-view/equivocation detection.
4. Move witness signing keys to KMS/HSM and publish independently signed checkpoints.
5. Add backup/restore, key rotation, trusted timestamp and incident-recovery drills.
6. Integrate historical signature verification only after the independent trust model is validated.
