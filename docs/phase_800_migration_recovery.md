# Phase 800 — Resumable Memory Migration & Failure Recovery

## Goal
Make an interrupted staging import recoverable without duplicating records or accepting a different source snapshot.

## Implemented
- `import_memory_snapshot` now accepts an empty target or a verified partial import from the exact same source file hash.
- Before resuming, every existing admission, record, and audit row is checked for source hash, source index, canonical record hash, fingerprint, and expected row counts.
- Existing validated records are skipped; only missing records are committed.
- A changed source, unrelated admission, malformed/duplicate index, proposal row, or inconsistent table counts fail closed.
- An `after_record` failure-injection seam supports interruption tests; it is not intended for external side effects.
- Final reconciliation checks that every source index exists and record counts match.
- Source JSON remains unchanged. Rollback export still refuses to overwrite an existing destination.

## Evidence added
- Simulated interruption after the first record, then successful resume without duplicate writes.
- Changed source after partial import is rejected.
- Existing count/hash, duplicate-record, backup-protection, malformed-input, and unrelated-target tests remain.

## Boundaries
This is a sequence of per-record atomic transactions, not one all-or-nothing transaction across the entire batch. Resume is safe only with the identical, unchanged source snapshot. Do not cut over until a real approved snapshot is verified, backup and restore are rehearsed, and an independent reviewer signs off.

**Production remains HOLD.**
