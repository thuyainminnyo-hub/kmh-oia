"""SQLite-backed idempotent storage for governed adaptation proposals.

This adapter is durable across process restarts and coordinates independent
processes sharing one SQLite database file. It is single-host/local-file storage,
not a shared multi-host production database.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


class AdaptationProposalConflict(ValueError):
    """Raised when one idempotency key is reused for different proposal content."""


class SQLiteAdaptationProposalRepository:
    """Persist proposals with a unique idempotency key and immutable content."""

    def __init__(self, path: str) -> None:
        if not isinstance(path, str) or not path.strip():
            raise ValueError("SQLite proposal repository path must be a non-empty file path")
        if path.strip() == ":memory:":
            raise ValueError("SQLite proposal repository requires a file-backed database")
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS adaptation_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    payload_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    @staticmethod
    def _payload(proposal: Any) -> dict[str, Any]:
        data = asdict(proposal) if hasattr(proposal, "__dataclass_fields__") else dict(proposal)
        # Status is mutable governance state, not part of immutable proposal content.
        return {key: value for key, value in data.items() if key != "status"}

    def get_or_create(self, proposal: Any, idempotency_key: str) -> dict[str, Any]:
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        data = asdict(proposal) if hasattr(proposal, "__dataclass_fields__") else dict(proposal)
        immutable = self._payload(data)
        payload_json = json.dumps(immutable, sort_keys=True, separators=(",", ":"))
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        proposal_id = str(data.get("id", "")).strip()
        if not proposal_id:
            raise ValueError("proposal id is required")
        status = str(data.get("status", "PROPOSED"))
        key = idempotency_key.strip()
        try:
            with self._connect() as connection:
                connection.execute(
                    """INSERT INTO adaptation_proposals
                       (proposal_id, idempotency_key, payload_hash, payload_json, status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (proposal_id, key, payload_hash, payload_json, status),
                )
                row = connection.execute(
                    "SELECT payload_json, status FROM adaptation_proposals WHERE idempotency_key = ?",
                    (key,),
                ).fetchone()
        except sqlite3.IntegrityError:
            with self._connect() as connection:
                row = connection.execute(
                    """SELECT proposal_id, payload_hash, payload_json, status
                       FROM adaptation_proposals WHERE idempotency_key = ?""",
                    (key,),
                ).fetchone()
                if row is None:
                    # A proposal ID collided with a different idempotency key.
                    raise AdaptationProposalConflict("proposal id already belongs to another event")
                existing_id, existing_hash, existing_json, existing_status = row
                if existing_hash != payload_hash or existing_id != proposal_id:
                    raise AdaptationProposalConflict(
                        "idempotency key already exists with conflicting proposal content"
                    )
                return {**json.loads(existing_json), "status": existing_status}
        except sqlite3.Error as exc:
            raise RuntimeError("durable adaptation proposal store unavailable") from exc
        if row is None:
            raise RuntimeError("proposal insert succeeded but canonical row could not be read")
        return {**json.loads(row[0]), "status": row[1]}

    def update_status(self, proposal_id: str, status: str) -> dict[str, Any]:
        transitions = {
            "APPROVED": "PROPOSED",
            "REJECTED": "PROPOSED",
            "APPLIED": "APPROVED",
        }
        if status not in transitions:
            raise ValueError("unsupported or non-transition status")
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """UPDATE adaptation_proposals SET status = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE proposal_id = ? AND status = ?""",
                    (status, proposal_id, transitions[status]),
                )
                if cursor.rowcount != 1:
                    raise ValueError("proposal status transition rejected or proposal not found")
                row = connection.execute(
                    """SELECT payload_json, status FROM adaptation_proposals
                       WHERE proposal_id = ?""",
                    (proposal_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise RuntimeError("durable adaptation proposal store unavailable") from exc
        if row is None:
            raise ValueError("proposal not found")
        return {**json.loads(row[0]), "status": row[1]}

    def get(self, idempotency_key: str) -> dict[str, Any] | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """SELECT payload_json, status FROM adaptation_proposals
                       WHERE idempotency_key = ?""",
                    (idempotency_key,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise RuntimeError("durable adaptation proposal store unavailable") from exc
        if row is None:
            return None
        return {**json.loads(row[0]), "status": row[1]}

    def health_check(self) -> bool:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("adaptation_proposals",),
                ).fetchone()
            return row is not None
        except sqlite3.Error:
            return False
