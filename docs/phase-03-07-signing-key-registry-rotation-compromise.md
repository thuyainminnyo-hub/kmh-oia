# Phase 03.07 — Signing Key Registry, Rotation & Compromise Response

**Status:** Registry/lifecycle functions and regression tests committed; exact latest CI pending.
**Date:** 2026-11-10
**Branch:** `phase-02-71/midi-golden-fixtures`

## Research basis and standards alignment

- NIST SP 800-57 Part 1 Rev. 5 remains the finalized guidance identified in NIST's publications catalogue. It describes pre-activation, active, suspended, deactivated, compromised and destroyed states and emphasizes recording lifecycle transitions. KMH's first registry is intentionally a smaller application-specific state machine: `pre_active`, `active`, `retired`, `compromised`, `revoked`. It is not a claim of full NIST state-model conformance.
- NIST SP 800-57 Part 1 Rev. 6 was published as an Initial Public Draft on 2025-12-05; public comments closed 2026-02-05. Do not call Rev. 6 a final standard unless NIST publishes a final version.
- OWASP Key Management guidance requires documented lifecycle, key compromise/recovery, secure storage, rotation, revocation checking and recovery procedures. OWASP Cryptographic Storage recommends dedicated vault/HSM/KMS where feasible and no source-control private keys.
- RFC 8032 defines Ed25519 key generation and signatures. RFC 9052 defines COSE key identifiers (`kid`) as lookup hints, not guaranteed globally unique identities; KMH therefore checks key ID plus SHA-256 fingerprint of the raw Ed25519 public key.

References:
- NIST SP 800-57 Rev. 5 final: https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- NIST SP 800-57 Rev. 6 initial public draft: https://csrc.nist.gov/pubs/sp/800/57/pt1/r6/ipd
- NIST key states: https://csrc.nist.gov/glossary/term/Key_states
- OWASP Key Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html
- OWASP Cryptographic Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
- RFC 8032: https://www.rfc-editor.org/rfc/rfc8032.html
- RFC 9052: https://www.rfc-editor.org/rfc/rfc9052.html

## Implementation

Added public-key registry schema `kmh.preservation-signing-key-registry.v1` and entry schema `kmh.preservation-signing-key.v1`.

New functions in `scripts/preservation_ingest.py`:
- `new_signing_key_registry()`
- `build_signing_key_registry_entry()` — records Ed25519 public key only, algorithm, SHA-256 fingerprint, creation/activation/optional signing-end timestamps, lifecycle state and initial history.
- `register_signing_key()` — rejects duplicate IDs and invalid key/fingerprint.
- `transition_signing_key()` — validates allowed lifecycle transitions, timezone-aware monotonic timestamps, required reason for retirement/compromise/revocation, and active replacement before normal retirement.
- `rotate_signing_key_registry()` — registers and activates replacement before retiring the prior active key.
- `compromise_signing_key()` — marks the old key compromised and can activate a replacement in the returned registry snapshot.
- `sign_recovery_approval_with_registry()` — checks active state, activation/expiry window, key ID and that supplied private key matches registered public key.
- `validate_signed_recovery_approval_with_registry()` — execution-oriented validation currently accepts active registry keys only; retired/compromised/revoked keys fail closed.

Regression tests cover registration, duplicate IDs, public-key fingerprint tampering, activation window, rotation, retirement linkage, compromise replacement, and key mismatch.

Commits:
- lifecycle implementation: `8d43ee4294cee67ed448e554efe07bdf3e92379c`
- registry lifecycle tests: `966251bd98ebd25466cf9c839707381bfbdcb12a`
- activation-window enforcement: `9bbac5e637f66ef21775d2c893679593d619d87f`
- premature-activation regression test: `58a9dd16dfda6315ada85b44a05ef2f63062706a`

## Important limitations

- Registry helpers return updated Python dictionaries; they do not provide durable storage, transactions, concurrency control, append-only tamper evidence, multi-admin approval or rollback resistance. `state_history` and `events` can be edited by a caller. Production needs a transactional datastore plus signed/hash-chained or externally witnessed audit records.
- No HSM/KMS/Vault integration exists. Private keys are still passed in by the caller. Registry stores public keys only.
- `sign_recovery_approval_with_registry` takes a registry entry object, so callers must source it from an authenticated/current registry snapshot; this helper alone is not a remote trust boundary.
- The execution validator rejects retired, compromised and revoked keys. Historical signature verification is a separate requirement: retired public keys should be retained for archive verification, while compromised-key signatures require trustworthy signing-time evidence (e.g., trusted timestamp/transparency proof) and a policy review. Do not infer historical validity from the record's self-asserted `approved_at` alone.
- Emergency compromise response should immediately stop new signing, revoke the key in the authoritative registry, identify approvals signed by that key, assess compromise time/uncertainty, provision a replacement from a trusted provider, and re-evaluate affected signatures. The helper's single returned snapshot is not a distributed atomic incident workflow.
- No recovery mutation executor is implemented or enabled. PR #217 remains OPEN / DRAFT; no production-readiness claim.

## Acceptance gates

1. Exact latest-commit CI passes OIA Tests, OIA Validation, MIDI Fixture Integrity, and Preservation Gate A on Linux and Windows.
2. Add independent tests for registry tampering, stale snapshots, concurrent rotation, invalid state history, replacement-key mismatch, and compromise of an already retired key.
3. Implement a durable transactional registry and append-only, independently witnessed key lifecycle audit.
4. Integrate a KMS/HSM/Vault-backed signing interface with key rotation/revocation and no private-key export to application code.
5. Add a distinct historical-signature verifier with trusted timestamp evidence and explicit compromised-key policy.
6. Only then consider registry-backed approval validation in any mutation-capable workflow.