"""SQLite-authoritative learning ledger with a transactional projection outbox.

This module is an additive persistence primitive. It is not wired into the
trusted-learning service yet; callers must not treat it as the active source
of truth until the service migration and recovery tests are complete.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


class LearningLedgerConflict(ValueError):
    """Raised when an event identity is reused with different immutable data."""


class SQLiteLearningLedger:
    """Atomically persist a learning event, proposal intent, and outbox message.

    One SQLite transaction is the authority boundary. JSON memory remains a
    downstream projection until the application service is migrated.
    """

    def __init__(self, path: str) -> None:
        if not isinstance(path, str) or not path.strip():
            raise ValueError("SQLite learning ledger path is required")
        if path.strip() == ":memory:" or path.strip().lower().startswith("file:"):
            raise ValueError("SQLite learning ledger requires a regular file path")
        self.path = str(Path(path).expanduser())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id TEXT PRIMARY KEY,
                    payload_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS learning_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL UNIQUE REFERENCES learning_events(event_id),
                    payload_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PROPOSED',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS learning_outbox (
                    event_id TEXT PRIMARY KEY REFERENCES learning_events(event_id),
                    message_json TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'PENDING'
                        CHECK (state IN ('PENDING', 'PROJECTED')),
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    lease_owner TEXT,
                    lease_token TEXT,
                    lease_until REAL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS learning_dead_letters (
                    event_id TEXT PRIMARY KEY REFERENCES learning_outbox(event_id),
                    attempts INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    quarantined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS learning_replay_audit (
                    replay_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    replayed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(learning_outbox)")
            }
            for name, definition in (
                ("lease_owner", "TEXT"),
                ("lease_token", "TEXT"),
                ("lease_until", "REAL"),
            ):
                if name not in columns:
                    connection.execute(
                        f"ALTER TABLE learning_outbox ADD COLUMN {name} {definition}"
                    )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _canonical_payload(payload: dict[str, Any], label: str) -> tuple[str, str]:
        if not isinstance(payload, dict) or not payload:
            raise ValueError(f"{label} must be a non-empty object")
        try:
            encoded = json.dumps(
                payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} must contain JSON-compatible values") from exc
        return encoded, hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def record_learning(
        self,
        *,
        event_id: str,
        event: dict[str, Any],
        proposal_id: str | None = None,
        proposal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Atomically create the event, optional proposal intent, and outbox row.

        Exact retries return the canonical persisted records. Reusing the event
        or proposal identity with changed immutable payload raises a conflict.
        """
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id is required")
        event_id = event_id.strip()
        event_json, event_hash = self._canonical_payload(event, "event")

        if (proposal_id is None) != (proposal is None):
            raise ValueError("proposal_id and proposal must be supplied together")
        proposal_json = proposal_hash = None
        if proposal is not None:
            if not isinstance(proposal_id, str) or not proposal_id.strip():
                raise ValueError("proposal_id is required")
            proposal_id = proposal_id.strip()
            proposal_json, proposal_hash = self._canonical_payload(proposal, "proposal")

        message = {
            "event_id": event_id,
            "event_hash": event_hash,
            "proposal_id": proposal_id,
            "proposal_hash": proposal_hash,
        }
        message_json, _ = self._canonical_payload(message, "outbox message")

        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    "SELECT payload_hash, payload_json FROM learning_events WHERE event_id = ?",
                    (event_id,),
                ).fetchone()
                if existing is None:
                    connection.execute(
                        "INSERT INTO learning_events(event_id, payload_hash, payload_json) VALUES (?, ?, ?)",
                        (event_id, event_hash, event_json),
                    )
                elif existing[0] != event_hash or existing[1] != event_json:
                    raise LearningLedgerConflict(
                        "event_id already exists with conflicting immutable event payload"
                    )

                if proposal is not None:
                    existing_proposal = connection.execute(
                        "SELECT event_id, payload_hash, payload_json FROM learning_proposals WHERE proposal_id = ?",
                        (proposal_id,),
                    ).fetchone()
                    if existing_proposal is None:
                        existing_for_event = connection.execute(
                            "SELECT proposal_id, payload_hash, payload_json FROM learning_proposals WHERE event_id = ?",
                            (event_id,),
                        ).fetchone()
                        if existing_for_event is not None:
                            raise LearningLedgerConflict(
                                "event_id already has a different canonical proposal"
                            )
                        connection.execute(
                            """INSERT INTO learning_proposals
                               (proposal_id, event_id, payload_hash, payload_json)
                               VALUES (?, ?, ?, ?)""",
                            (proposal_id, event_id, proposal_hash, proposal_json),
                        )
                    elif (
                        existing_proposal[0] != event_id
                        or existing_proposal[1] != proposal_hash
                        or existing_proposal[2] != proposal_json
                    ):
                        raise LearningLedgerConflict(
                            "proposal_id already exists with conflicting immutable content"
                        )

                connection.execute(
                    """INSERT INTO learning_outbox(event_id, message_json)
                       VALUES (?, ?)
                       ON CONFLICT(event_id) DO NOTHING""",
                    (event_id, message_json),
                )
                canonical = connection.execute(
                    """SELECT e.payload_json, p.proposal_id, p.payload_json, o.state, o.attempts
                       FROM learning_events e
                       LEFT JOIN learning_proposals p ON p.event_id = e.event_id
                       JOIN learning_outbox o ON o.event_id = e.event_id
                       WHERE e.event_id = ?""",
                    (event_id,),
                ).fetchone()
                if canonical is None:
                    raise RuntimeError("learning ledger transaction did not produce canonical rows")
                return {
                    "event": json.loads(canonical[0]),
                    "proposal_id": canonical[1],
                    "proposal": json.loads(canonical[2]) if canonical[2] else None,
                    "outbox_state": canonical[3],
                    "outbox_attempts": canonical[4],
                }
        except sqlite3.Error as exc:
            raise RuntimeError("durable SQLite learning ledger unavailable") from exc

    def pending_outbox(self, limit: int = 100) -> tuple[dict[str, Any], ...]:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("limit must be a positive integer")
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT event_id, message_json, attempts
                   FROM learning_outbox
                   WHERE state = 'PENDING'
                     AND NOT EXISTS (
                         SELECT 1 FROM learning_dead_letters d
                         WHERE d.event_id = learning_outbox.event_id
                     )
                   ORDER BY created_at, event_id LIMIT ?""",
                (limit,),
            ).fetchall()
        return tuple(
            {"event_id": row[0], "message": json.loads(row[1]), "attempts": row[2]}
            for row in rows
        )

    def claim_pending(self, *, worker_id: str, limit: int = 100, lease_seconds: int = 60) -> tuple[dict[str, Any], ...]:
        """Atomically claim pending or expired-lease rows for one worker."""
        import time
        import uuid

        if not isinstance(worker_id, str) or not worker_id.strip():
            raise ValueError("worker_id is required")
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("limit must be a positive integer")
        if not isinstance(lease_seconds, int) or isinstance(lease_seconds, bool) or lease_seconds < 1:
            raise ValueError("lease_seconds must be a positive integer")
        now = time.time()
        claimed = []
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                rows = connection.execute(
                    """SELECT event_id, message_json, attempts FROM learning_outbox
                       WHERE state = 'PENDING' AND (lease_until IS NULL OR lease_until <= ?)
                         AND NOT EXISTS (
                             SELECT 1 FROM learning_dead_letters d
                             WHERE d.event_id = learning_outbox.event_id
                         )
                       ORDER BY created_at, event_id LIMIT ?""",
                    (now, limit),
                ).fetchall()
                for event_id, message_json, attempts in rows:
                    token = uuid.uuid4().hex
                    cursor = connection.execute(
                        """UPDATE learning_outbox
                           SET lease_owner = ?, lease_token = ?, lease_until = ?,
                               updated_at = CURRENT_TIMESTAMP
                           WHERE event_id = ? AND state = 'PENDING'
                             AND (lease_until IS NULL OR lease_until <= ?)""",
                        (worker_id.strip(), token, now + lease_seconds, event_id, now),
                    )
                    if cursor.rowcount == 1:
                        claimed.append({
                            "event_id": event_id,
                            "message": json.loads(message_json),
                            "attempts": attempts,
                            "worker_id": worker_id.strip(),
                            "claim_token": token,
                        })
            return tuple(claimed)
        except sqlite3.Error as exc:
            raise RuntimeError("durable SQLite learning ledger unavailable") from exc

    def release_claim(self, event_id: str, *, claim_token: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE learning_outbox SET lease_owner = NULL, lease_token = NULL,
                   lease_until = NULL, updated_at = CURRENT_TIMESTAMP
                   WHERE event_id = ? AND state = 'PENDING' AND lease_token = ?""",
                (event_id, claim_token),
            )
            return cursor.rowcount == 1

    def mark_projected(self, event_id: str, *, claim_token: str | None = None) -> None:
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id is required")
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE learning_outbox
                   SET state = 'PROJECTED', attempts = attempts + 1,
                       last_error = NULL, lease_owner = NULL, lease_token = NULL,
                       lease_until = NULL, updated_at = CURRENT_TIMESTAMP
                   WHERE event_id = ? AND state = 'PENDING'
                     AND (? IS NULL OR lease_token = ?)""",
                (event_id.strip(), claim_token, claim_token),
            )
            if cursor.rowcount != 1:
                row = connection.execute(
                    "SELECT state FROM learning_outbox WHERE event_id = ?",
                    (event_id.strip(),),
                ).fetchone()
                if row is None:
                    raise ValueError("outbox event not found")
                if row[0] != "PROJECTED":
                    raise RuntimeError("outbox projection state transition failed")

    def record_projection_failure(
        self, event_id: str, error: str, *, claim_token: str | None = None,
        max_attempts: int = 5,
    ) -> int:
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id is required")
        if not isinstance(error, str) or not error.strip():
            raise ValueError("projection error is required")
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """UPDATE learning_outbox
                   SET attempts = attempts + 1, last_error = ?,
                       lease_owner = NULL, lease_token = NULL, lease_until = NULL,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE event_id = ? AND state = 'PENDING'
                     AND (? IS NULL OR lease_token = ?)""",
                (error.strip()[:1000], event_id.strip(), claim_token, claim_token),
            )
            if cursor.rowcount != 1:
                raise ValueError("pending outbox event not found or claim token is stale")
            attempts = connection.execute(
                "SELECT attempts FROM learning_outbox WHERE event_id = ?",
                (event_id.strip(),),
            ).fetchone()[0]
            if attempts >= max_attempts:
                connection.execute(
                    """INSERT INTO learning_dead_letters(event_id, attempts, reason)
                       VALUES (?, ?, ?)
                       ON CONFLICT(event_id) DO UPDATE SET
                           attempts = excluded.attempts, reason = excluded.reason,
                           quarantined_at = CURRENT_TIMESTAMP""",
                    (event_id.strip(), attempts, error.strip()[:1000]),
                )
            return attempts

    def replay_dead_letter(self, event_id: str, *, actor: str, reason: str) -> None:
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id is required")
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError("actor is required")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("replay reason is required")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT event_id FROM learning_dead_letters WHERE event_id = ?",
                (event_id.strip(),),
            ).fetchone()
            if row is None:
                raise ValueError("dead-letter event not found")
            connection.execute(
                """INSERT INTO learning_replay_audit(event_id, actor, reason)
                   VALUES (?, ?, ?)""",
                (event_id.strip(), actor.strip(), reason.strip()[:1000]),
            )
            connection.execute(
                "DELETE FROM learning_dead_letters WHERE event_id = ?",
                (event_id.strip(),),
            )
            connection.execute(
                """UPDATE learning_outbox SET attempts = 0, last_error = NULL,
                   lease_owner = NULL, lease_token = NULL, lease_until = NULL,
                   updated_at = CURRENT_TIMESTAMP WHERE event_id = ?""",
                (event_id.strip(),),
            )

    def dead_letters(self, limit: int = 100) -> tuple[dict[str, Any], ...]:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("limit must be a positive integer")
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT event_id, attempts, reason, quarantined_at
                   FROM learning_dead_letters ORDER BY quarantined_at, event_id LIMIT ?""",
                (limit,),
            ).fetchall()
        return tuple(
            {"event_id": row[0], "attempts": row[1], "reason": row[2], "quarantined_at": row[3]}
            for row in rows
        )

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM learning_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def get_projection_bundle(self, event_id: str) -> dict[str, Any]:
        """Return a hash-verified immutable bundle for an outbox projection."""
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id is required")
        with self._connect() as connection:
            row = connection.execute(
                """SELECT e.payload_hash, e.payload_json, p.proposal_id,
                          p.payload_hash, p.payload_json, o.message_json, o.state
                   FROM learning_events e
                   JOIN learning_outbox o ON o.event_id = e.event_id
                   LEFT JOIN learning_proposals p ON p.event_id = e.event_id
                   WHERE e.event_id = ?""",
                (event_id.strip(),),
            ).fetchone()
        if row is None:
            raise ValueError("learning outbox event not found")
        event_hash, event_json, proposal_id, proposal_hash, proposal_json, message_json, state = row
        event = json.loads(event_json)
        _, actual_event_hash = self._canonical_payload(event, "event")
        message = json.loads(message_json)
        if actual_event_hash != event_hash or message.get("event_id") != event_id.strip():
            raise LearningLedgerConflict("outbox event identity or payload hash mismatch")
        if message.get("event_hash") != event_hash:
            raise LearningLedgerConflict("outbox event hash does not match canonical event")
        proposal = json.loads(proposal_json) if proposal_json else None
        if proposal is None:
            if proposal_id is not None or message.get("proposal_id") is not None:
                raise LearningLedgerConflict("outbox proposal identity mismatch")
            if message.get("proposal_hash") is not None:
                raise LearningLedgerConflict("unexpected outbox proposal hash")
        else:
            _, actual_proposal_hash = self._canonical_payload(proposal, "proposal")
            if actual_proposal_hash != proposal_hash:
                raise LearningLedgerConflict("canonical proposal payload hash mismatch")
            if message.get("proposal_id") != proposal_id or message.get("proposal_hash") != proposal_hash:
                raise LearningLedgerConflict("outbox proposal identity or hash mismatch")
        return {
            "event_id": event_id.strip(), "event": event,
            "proposal_id": proposal_id, "proposal": proposal,
            "state": state, "message": message,
        }

    def health_check(self) -> bool:
        try:
            with self._connect() as connection:
                result = connection.execute("PRAGMA integrity_check").fetchone()
                tables = {
                    row[0] for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
            return result == ("ok",) and {
                "learning_events", "learning_proposals", "learning_outbox",
                "learning_dead_letters", "learning_replay_audit"
            }.issubset(tables)
        except sqlite3.Error:
            return False
