# Phase 03.05 — Signed Recovery Approval & Replay Guard

**Status:** Ed25519 approval signing and validation functions implemented; regression tests added; exact latest-commit CI pending.
**Date:** 2026-11-10
**Branch:** `phase-02-71/midi-golden-fixtures`

## Research basis

- RFC 8032 specifies Ed25519 signatures. KMH uses Ed25519 to sign approval-record bytes; signatures provide integrity/authenticity relative to a trusted public-key registry, not proof of human identity by themselves.
- RFC 8785 defines JSON Canonicalization Scheme (JCS). Current KMH uses Python `json.dumps(sort_keys=True, separators=(',', ':'))`; this is deterministic for the supported Python data used in tests, but is NOT claimed to be RFC 8785 conformant or cross-language canonical. Before multi-language clients sign/verify, adopt a tested RFC 8785 implementation or a specified deterministic CBOR/COSE profile.
- RFC 9052 defines COSE structures including COSE_Sign1; a future interoperable signed envelope could use COSE rather than a project-specific JSON envelope.
- NIST SP 800-57 Part 1 Rev. 5 provides key-management lifecycle guidance: generation, protection, distribution, use, rotation, archival and destruction. Private signing keys must remain outside source control and ordinary application config.
- RFC 9162 provides a Merkle-tree transparency-log model. It can inform tamper-evident audit publication, but does not itself provide trusted operator authentication or transactional recovery semantics.

References:
- Ed25519 / RFC 8032: https://www.rfc-editor.org/rfc/rfc8032.html
- JSON Canonicalization / RFC 8785: https://www.rfc-editor.org/rfc/rfc8785.html
- COSE / RFC 9052: https://www.rfc-editor.org/rfc/rfc9052.html
- NIST SP 800-57 Part 1 Rev. 5: https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- Transparency Logs / RFC 9162: https://www.rfc-editor.org/rfc/rfc9162.html

## Implementation

Added dependency to `requirements-preservation.txt`: `cryptography>=44.0,<47.0`.

Added functions in `scripts/preservation_ingest.py`:
- `sign_recovery_approval_record(record, private_key, key_id)` — signs a canonicalized approval copy with Ed25519; algorithm and key ID are included in signed bytes.
- `validate_signed_recovery_approval(...)` — verifies algorithm, trusted key ID, Ed25519 signature, exact plan and journal digest binding, allowlisted action, approval/expiry time, injected actor authorization, and an injected nonce-consumption callback.
- Approval records now include a cryptographically random nonce.
- Approval validation rejects future-dated approval timestamps, naive timestamps, expired approvals, and invalid time order.

Regression tests cover:
- valid Ed25519 signature and successful nonce consumption;
- modified actor field/signature tampering;
- signing-key ID substitution;
- untrusted signing key;
- nonce-store unavailable and replay/nonce callback rejection;
- future-dated approval timestamp;
- existing plan binding, actor authorization, disallowed action and expiry checks.

Commits:
- cryptography dependency: `164654495543eada860a93c4b9d5d66d1f308249`
- Ed25519 signer and validation: `c22f10ecaf5939299a112f153b761cd86fd2e111`
- signed-approval tests: `4e3930f5fb2dc725a88b83139a20b0ac913916a9`
- bind key ID and algorithm into signature: `8e61c15b786ae45e9de506661414d00f650b466d`
- key-substitution/replay tests: `970ef554a267a15743b8622df013e873cf95a34c`
- reject future-dated approvals: `1dee738c7411086cf4c1304edb8d6b8ae34d8f85`
- future-time regression test: `8dcb490b21a52c084280d9a6a1ddf036e5000514`

## Critical operational contract

- The private key is supplied as an `Ed25519PrivateKey` object by the caller. No HSM, KMS, OS keychain, encrypted keystore or key rotation integration is implemented.
- Trusted public keys are passed in by the caller. A managed key registry, activation windows, revocation, compromise handling and rotation are not implemented.
- `consume_nonce(approval_id, nonce)` MUST be backed by durable, atomic, unique storage (for example a transactional database with a unique constraint). The callback must atomically reserve/consume the approval ID and nonce; an in-memory callback is not sufficient in production.
- Exactly-once execution cannot be assumed across crashes. Before any mutation, build a durable recovery transaction ledger with states such as `approved → reserved → executing → completed/failed`, and make each action idempotent. A crash after a side effect but before recording completion must be safely reconcilable.
- `actor_id` remains an identity claim; a trusted identity provider and authorization service are still required.
- Current canonical JSON is not RFC 8785 JCS. Do not claim cross-language signature interoperability until this is replaced and tested against RFC 8785 vectors.
- No recovery mutation executor is implemented or enabled. These functions only create and validate approvals.

## Next steps

1. Run exact latest-commit CI and inspect Linux/Windows logs.
2. Replace ad hoc canonical JSON with RFC 8785 JCS (or specify a COSE deterministic-CBOR profile) and add published test vectors.
3. Integrate a real key provider, trusted key registry, key rotation and revocation policy.
4. Implement a durable transactional nonce/idempotency ledger with unique constraints and crash recovery.
5. Integrate a real operator identity provider and permission policy.
6. Only after all gates pass, design the controlled recovery executor; keep mutation disabled meanwhile.

PR #217 remains OPEN / DRAFT. Gate A remains open. No production-readiness or power-loss durability claim.