"""Read-only, PII-minimizing SQLite runtime inventory for EduAutomate.

This utility reports metadata and aggregate counts only. It never selects
payment/student records, and opens an existing database using SQLite mode=ro.
It does not prove that the selected file is the active runtime database;
confirm the path with the runtime owner before running it.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = "runtime/eduautomate-payments.sqlite3"
KNOWN_PAYMENT_STATUSES = {"pending", "confirmed", "rejected"}
UNKNOWN_STATUS_LABEL = "other_or_invalid"


def audit_database(db_path: str | Path) -> dict[str, Any]:
    path = Path(db_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError("Database file not found at the configured path")

    result: dict[str, Any] = {
        "file_exists": True,
        "file_name": path.name,
        "file_size_bytes": path.stat().st_size,
        "tables": [],
        "payments_table_found": False,
        "payments_columns": [],
        "tenant_id_column_present": False,
        "payment_row_count": None,
        "payment_status_counts": {},
    }

    # as_uri() safely encodes spaces and other URI-sensitive path characters.
    uri = path.as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, timeout=5)) as conn:
        conn.execute("PRAGMA query_only=ON")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        result["tables"] = tables

        if "payments" not in tables:
            return result

        result["payments_table_found"] = True
        cursor.execute("PRAGMA table_info(payments)")
        columns = [row[1] for row in cursor.fetchall()]
        result["payments_columns"] = columns
        result["tenant_id_column_present"] = "tenant_id" in columns

        cursor.execute("SELECT COUNT(*) FROM payments")
        result["payment_row_count"] = int(cursor.fetchone()[0])

        if "status" in columns:
            cursor.execute(
                "SELECT status, COUNT(*) FROM payments "
                "GROUP BY status ORDER BY status"
            )
            # Never echo arbitrary status values from legacy/unconstrained schemas.
            # Unexpected values are collapsed into one safe bucket to minimize PII leakage.
            counts: dict[str, int] = {}
            for status, count in cursor.fetchall():
                label = status if isinstance(status, str) and status in KNOWN_PAYMENT_STATUSES else UNKNOWN_STATUS_LABEL
                counts[label] = counts.get(label, 0) + int(count)
            result["payment_status_counts"] = dict(sorted(counts.items()))

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-path",
        default=os.environ.get("EDUAUTOMATE_DB_PATH", DEFAULT_DB_PATH),
        help="Exact database path confirmed by the runtime owner; defaults to "
        "EDUAUTOMATE_DB_PATH or runtime/eduautomate-payments.sqlite3.",
    )
    args = parser.parse_args()

    try:
        report = audit_database(args.db_path)
    except FileNotFoundError:
        print(
            json.dumps(
                {
                    "audit_status": "NOT_RUN_DATABASE_NOT_FOUND",
                    "warning": (
                        "This path was not found. This does not prove legacy data "
                        "is absent from other paths, databases, or exports."
                    ),
                },
                indent=2,
            )
        )
        return 2
    except (sqlite3.Error, OSError) as exc:
        print(json.dumps({
            "audit_status": "ERROR",
            "error_type": type(exc).__name__,
        }, indent=2))
        return 3

    report["audit_status"] = "COMPLETED_READ_ONLY"
    report["warning"] = (
        "Metadata for this path only; confirm it is the active runtime database. "
        "No ownership or production-readiness conclusion is implied."
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
