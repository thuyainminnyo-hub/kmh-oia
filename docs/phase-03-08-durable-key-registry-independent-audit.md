# Phase 03.08 — Durable Signing Key Registry & Independent Audit Prototype

**Status:** SQLite implementation and 661-test suite passed; latest Preservation Gate A Windows conformance was still running at documentation time.
**Date:** 2026-11-10
**Branch:** `phase-02-71/midi-golden-fixtures`

## Research basis

- NIST SP 800-57 Part 2 Rev. 1: organization, policy, practice statement and infrastructure for key management.
- SQLite transaction documentation: explicit transactions and `BEGIN IMMEDIATE` serialize writers; WAL permits concurrent readers and a writer; `synchronous=FULL` requests stronger commit durability.
- RFC 9162: Merkle transparency logs provide independently verifiable append-only structures and consistency proofs. KMH's current SHA-256 hash chain is only a local prototype and is not an RFC 9162 implementation.
- RFC 8785 JCS canonicalization is used for event bytes before hashing.
- References:
  - https://csrc.nist.gov/pubs/sp/800/57/pt2/r1/final
  - https://www.sqlite.org/lang_transaction.html
  - https://www.sqlite.org/wal.html
  - https://www.sqlite.org/pragma.html#pragma_synchronous
  - https://www.rfc-editor.org/rfc/rfc9162.html
  - https://www.rfc-editor.org/rfc/rfc8785.html

## Implementation

New module: `scripts/signing_key_registry.py`

Class: `DurableSigningKeyRegistry`

Features:
- SQLite schema versioning and durable file-backed storage.
- WAL journal mode for file-backed DB.
- `synchronous=FULL`, foreign keys and busy timeout configured per connection.
- `BEGIN IMMEDIATE` transaction wrapper for each mutation.
- Public-key registry entries persisted as canonical JSON; private keys are never stored.
- Atomic rotation: replacement registration, activation, old-key retirement and corresponding audit events commit or roll back together.
- Lifecycle transitions enforce state rules, reason requirements, activation windows and replacement-before-retirement.
- Append-only audit table protected by SQLite UPDATE/DELETE triggers.
- Each audit event includes previous hash; SHA-256 event hash chains canonical RFC 8785 bytes.
- Startup checks database schema version.
- Audit-chain verification helper.
- Execution key listing requires caller-supplied trusted time and returns active, eligible public keys only.

New test file: `tests/test_signing_key_registry.py`

Coverage:
- persistence across independent registry instances/reopen;
- atomic successful rotation;
- failed rotation rollback of key rows and audit rows;
- append-only audit UPDATE/DELETE rejection;
- durable compromise state blocks execution-key listing;
- audit-chain verification.

Commits:
- SQLite registry module: `de961cb79f2c9788550c7d94ff680e41907d5f7c`
- trusted-time and rotation reason fix: `4c01ffb128bbf7e86cde3bcb8851aac03b87deb4`
- durable registry tests: `96eeac3765d93751d81691124089dac54de47ac7`

## CI evidence for exact test commit

Commit `96eeac3765d93751d81691124089dac54de47ac7`:
- KMH OIA Tests run `42735298946`: SUCCESS, 661 tests passed; all five durable registry tests passed.
- KMH OIA Validation run `42735299228`: SUCCESS.
- KMH MIDI Fixture Integrity run `42735298867`: SUCCESS.
- KMH Preservation Gate A run `42735299058`: Linux bagit-intake SUCCESS; Windows conformance was still running at the time checked. Do not claim the exact commit's full Gate A complete until Windows is green.

## Critical limitations

- SQLite triggers and local hash chain do not protect against a privileged database owner who can replace the DB, alter schema/triggers, or rewrite all rows. No external witness, remote append-only service, signed checkpoints, or Merkle consistency proofs exist.
- This is a single-host local durable prototype, not a distributed registry. No cross-region replication, backup/restore verification, multi-admin approval, or disaster recovery has been implemented.
- SQLite WAL and FULL synchronous settings do not replace storage-level guarantees, tested backup procedures, filesystem/device integrity, or operational monitoring.
- The API's caller-supplied timestamp must come from a trusted clock service in production.
- No KMS/HSM/Vault integration or private-key custody interface exists.
- No historical signature adjudicator or RFC 9162 transparency log exists.
- No recovery mutation executor is enabled. PR #217 remains OPEN / DRAFT. No production-readiness claim.

## Next acceptance gates

1. Confirm exact latest commit's Windows Preservation Gate A.
2. Add multi-process concurrent rotation tests and stale-snapshot/optimistic-version checks.
3. Add backup/restore drills, corruption detection, WAL checkpoint policy and filesystem permission guidance.
4. Export signed audit checkpoints to an independently controlled witness; then evaluate an RFC 9162 Merkle log.
5. Integrate KMS/HSM/Vault key custody and trusted time source.
6. Add historical signature verification with explicit policy for retired and compromised keys.
