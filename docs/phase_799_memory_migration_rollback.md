# Phase 799 — Legacy Memory Migration & Rollback Prototype

## Scope
Adds a non-destructive helper for importing JSON-backed `OperatingMemory` records into an empty staging SQLite repository. It does not inspect, alter, or cut over any production memory file.

## Implemented
- Validates source JSON list and each record schema.
- Captures SHA-256 of original file bytes and each canonical record.
- Preserves exact duplicate records by including source index in the idempotency key.
- Stores historical rows with `LEGACY_MEMORY_IMPORTED` audit events and creates no adaptation proposals.
- Exports only marked legacy-import rows to a new destination; refuses to overwrite an existing backup.
- Never deletes or rewrites the original source JSON.

## Test coverage
- Count/hash reconciliation and source byte preservation.
- Duplicate record preservation.
- Rollback export hash comparison.
- Existing destination protection.
- Malformed JSON fails closed before database writes.
- Non-empty staging target rejected.

## Limits
- This is a staging prototype; real project legacy data has not been migrated or verified.
- Whole-batch import is not yet atomic. If a batch fails partway through, discard the staging database and restart from a fresh staging copy. Never cut over a partial staging database.
- Local-filesystem SQLite only; no shared multi-host guarantee.
- Real backup/restore rehearsal, production source reconciliation, provider authenticity, target runtime deployment, and independent review remain open.

**Production remains HOLD.**
