# Phase 957 — Runtime DB audit runbook

## Purpose and boundary

Collect minimal, read-only metadata from an **owner-confirmed Local or Staging SQLite database**. This procedure does not establish ownership, tenant safety, or production readiness. Do not run it against Production for Phase 957.

## Preconditions

- Runtime owner confirms the exact database file used by the selected Local/Staging instance.
- Use an authorized host/session and follow the environment's data-handling policy.
- Do not place credentials, database copies, connection strings, or raw payment/student records in tickets or chat.
- If the active store is not SQLite, stop and document the actual engine; do not point this utility at another file format.

## Run

From the checked-out repository, on the approved Local/Staging host:

```bash
python scripts/audit_runtime_db.py --db-path "/OWNER-CONFIRMED/LOCAL-OR-STAGING/PATH.sqlite3"
```

Use the actual path locally; do not commit it to source control or paste it into a public issue. The script uses SQLite URI `mode=ro` and `PRAGMA query_only=ON`.

If the runtime owner has explicitly confirmed that `EDUAUTOMATE_DB_PATH` is set correctly in the selected environment, this is also supported:

```bash
python scripts/audit_runtime_db.py
```

## Report only sanitized metadata

Share only:
- environment label (`Local` or `Staging`)
- confirmation that the path was verified by the runtime owner (yes/no)
- `audit_status`
- `file_exists` and `file_size_bytes`, if present
- table names and payment column names
- `tenant_id_column_present`
- `payment_row_count`
- `payment_status_counts`

Do not share the database file, raw rows, payment/student identifiers or names, secrets, credentials, connection strings, or an unredacted path if it reveals sensitive infrastructure details.

## Interpret results conservatively

- `COMPLETED_READ_ONLY` means the selected file was inspected read-only; it does not prove the path is the only or active data store unless the runtime owner confirms that.
- `NOT_RUN_DATABASE_NOT_FOUND` means only that the configured path was not found. It does **not** prove there is no legacy data elsewhere.
- Missing `tenant_id` means this inspected schema does not contain that column; it does not authorize inferred ownership or backfill.
- Status counts expose only the known labels `pending`, `confirmed`, and `rejected`; all other/null legacy status values are grouped under `other_or_invalid` to avoid echoing arbitrary database text. Aggregate row/status counts are inventory evidence only. They do not establish payment-to-tenant ownership.
- If the file is locked, corrupt, inaccessible, or not SQLite, stop and report only the sanitized error type/status; do not attempt repair or migration.

## Release gates still required

1. Independent review of PR #114 at the exact reviewed commit.
2. Runtime owner confirms the selected Local/Staging path and provides sanitized output.
3. Registry Owner supplies authoritative legacy payment-to-tenant mapping, or records that no safe mapping is available and affected records remain quarantined.
4. Identity owner confirms the signed token `user_id` claim contract.
5. Separate approved migration rehearsal, rollback plan, tenant-isolation tests, and release approval before any production change.

**Production HOLD remains.** This utility is inventory-only; it performs no schema changes, backfills, unquarantine, route activation, or deployment.
