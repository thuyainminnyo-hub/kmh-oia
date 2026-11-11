"""SQLite-backed hash-chained audit sink for the KMH OIA local pilot.

This provides durable local evidence and detects accidental or unauthorized row
changes while the schema/triggers remain intact. It is NOT a remotely anchored,
WORM, or independently administered audit service.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from threading import RLock

from src.agent_trust import AuditEvent


_GENESIS = "0" * 64


class SQLiteHashChainAudit:
    """Durable append-only audit sink with a verifiable SHA-256 hash chain."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self._lock = RLock()
        self._connection = sqlite3.connect(
            self.database_path, check_same_thread=False, isolation_level=None
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                sequence INTEGER PRIMARY KEY,
                event_json TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL UNIQUE
            );
            CREATE TRIGGER IF NOT EXISTS audit_events_no_update
            BEFORE UPDATE ON audit_events
            BEGIN SELECT RAISE(ABORT, 'audit events are append-only'); END;
            CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
            BEFORE DELETE ON audit_events
            BEGIN SELECT RAISE(ABORT, 'audit events are append-only'); END;
            """
        )

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT event_json FROM audit_events ORDER BY sequence"
            ).fetchall()
            return tuple(AuditEvent(**json.loads(row["event_json"])) for row in rows)

    def append(self, event: AuditEvent) -> None:
        payload = json.dumps(asdict(event), sort_keys=True, separators=(",", ":"))
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute(
                    "SELECT sequence, event_hash FROM audit_events "
                    "ORDER BY sequence DESC LIMIT 1"
                ).fetchone()
                expected_sequence = 1 if row is None else int(row["sequence"]) + 1
                previous_hash = _GENESIS if row is None else str(row["event_hash"])
                if event.sequence != expected_sequence:
                    raise ValueError("audit sequence must be contiguous")
                digest = hashlib.sha256(
                    (previous_hash + "\n" + payload).encode("utf-8")
                ).hexdigest()
                self._connection.execute(
                    "INSERT INTO audit_events "
                    "(sequence, event_json, previous_hash, event_hash) VALUES (?, ?, ?, ?)",
                    (event.sequence, payload, previous_hash, digest),
                )
                self._connection.execute("COMMIT")
            except Exception:
                self._connection.execute("ROLLBACK")
                raise

    def verify_chain(self) -> bool:
        """Verify sequence continuity, predecessor links and every event digest."""
        with self._lock:
            rows = self._connection.execute(
                "SELECT sequence, event_json, previous_hash, event_hash "
                "FROM audit_events ORDER BY sequence"
            ).fetchall()
            previous_hash = _GENESIS
            for expected_sequence, row in enumerate(rows, start=1):
                if int(row["sequence"]) != expected_sequence:
                    return False
                if row["previous_hash"] != previous_hash:
                    return False
                digest = hashlib.sha256(
                    (previous_hash + "\n" + row["event_json"]).encode("utf-8")
                ).hexdigest()
                if digest != row["event_hash"]:
                    return False
                previous_hash = digest
            return True

    def close(self) -> None:
        with self._lock:
            self._connection.close()
