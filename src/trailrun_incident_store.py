"""SQLite-backed pilot incident store with transactional idempotency.

This is a local single-host persistence adapter for development and controlled
testing. It is NOT a multi-host database, production dispatch service, or
authorization layer. Validate input against incident.schema.json and authorize
the caller at the service boundary before invoking this module.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.trailrun_incident_access import authorize_transition
from src.trailrun_incident_state_machine import validate_transition

ALLOWED_STATUSES = {
    "REPORTED", "ACKNOWLEDGED", "DISPATCHED", "RESOLVED", "CLOSED"
}


class IncidentStoreError(Exception):
    """Base exception for incident-store failures."""


class IdempotencyConflict(IncidentStoreError):
    """An event ID was reused with a different payload."""


class IncidentNotFound(IncidentStoreError):
    """The requested incident does not exist."""


class InvalidIncident(IncidentStoreError):
    """The incident payload fails minimal storage-boundary checks."""


class InvalidTransition(IncidentStoreError):
    """A requested state transition is not allowed."""


@dataclass(frozen=True)
class CreateResult:
    incident_id: str
    event_id: str
    created: bool


class SQLiteIncidentStore:
    """Small durable store using one SQLite transaction per operation."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        if self.database_path == ":memory:":
            raise ValueError("Use a file-backed database to verify restart persistence")
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS event_receipts (
                    event_id TEXT PRIMARY KEY,
                    payload_sha256 TEXT NOT NULL,
                    incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS incident_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
                    action TEXT NOT NULL,
                    actor_role TEXT NOT NULL,
                    at TEXT NOT NULL,
                    result TEXT NOT NULL,
                    correlation_id TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_incident_audit_incident
                    ON incident_audit(incident_id, sequence);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path, timeout=10.0, isolation_level=None
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    @staticmethod
    def _canonical_json(payload: dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _validate_minimum_payload(payload: dict[str, Any]) -> None:
        required = {
            "incident_id", "event_id", "status", "recorded_at",
            "reported_by_role", "audit",
        }
        if not isinstance(payload, dict) or not required.issubset(payload):
            raise InvalidIncident("Missing required incident fields")
        if payload["status"] != "REPORTED":
            raise InvalidIncident("New incidents must start in REPORTED state")
        if not isinstance(payload["audit"], list) or not payload["audit"]:
            raise InvalidIncident("At least one initial audit entry is required")
        if payload["audit"][0].get("action") != "REPORTED":
            raise InvalidIncident("First audit entry must record REPORTED")

    def create_incident(self, payload: dict[str, Any]) -> CreateResult:
        """Create once per event_id; exact replay returns the original receipt."""
        self._validate_minimum_payload(payload)
        canonical = self._canonical_json(payload)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        incident_id = str(payload["incident_id"])
        event_id = str(payload["event_id"])
        created_at = str(payload["recorded_at"])

        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT payload_sha256, incident_id FROM event_receipts WHERE event_id=?",
                (event_id,),
            ).fetchone()
            if existing:
                connection.rollback()
                if existing["payload_sha256"] != digest:
                    raise IdempotencyConflict(
                        "event_id was already used with a different payload"
                    )
                return CreateResult(existing["incident_id"], event_id, False)

            connection.execute(
                "INSERT INTO incidents(incident_id, status, payload_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (incident_id, "REPORTED", canonical, created_at),
            )
            connection.execute(
                "INSERT INTO event_receipts(event_id, payload_sha256, incident_id, created_at) "
                "VALUES (?, ?, ?, ?)",
                (event_id, digest, incident_id, created_at),
            )
            first = payload["audit"][0]
            connection.execute(
                "INSERT INTO incident_audit(incident_id, action, actor_role, at, result, correlation_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    incident_id, first["action"], first["actor_role"], first["at"],
                    first["result"], first.get("correlation_id"),
                ),
            )
            connection.commit()
        return CreateResult(incident_id, event_id, True)

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT incident_id, status, payload_json, created_at FROM incidents WHERE incident_id=?",
                (incident_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "incident_id": row["incident_id"],
            "status": row["status"],
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
        }

    def transition(
        self,
        incident_id: str,
        requested_status: str,
        *,
        actor_role: str,
        at: str,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        """Atomically change status and append its audit entry."""
        if not actor_role or not at:
            raise InvalidIncident("actor_role and timestamp are required")
        if requested_status not in ALLOWED_STATUSES:
            raise InvalidTransition("Unknown requested status")
        # Defense in depth: direct store callers must not bypass transition policy.
        # This is not authentication; actor_role must still come from a trusted principal.
        access = authorize_transition(actor_role, requested_status)
        if not access.allowed:
            raise InvalidTransition(access.reason_code)

        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT status FROM incidents WHERE incident_id=?", (incident_id,)
            ).fetchone()
            if row is None:
                connection.rollback()
                raise IncidentNotFound(incident_id)

            current_status = row["status"]
            decision = validate_transition(current_status, requested_status)
            if not decision.allowed:
                connection.rollback()
                raise InvalidTransition(decision.reason_code)

            connection.execute(
                "UPDATE incidents SET status=? WHERE incident_id=? AND status=?",
                (requested_status, incident_id, current_status),
            )
            connection.execute(
                "INSERT INTO incident_audit(incident_id, action, actor_role, at, result, correlation_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    incident_id, requested_status, actor_role, at, "completed",
                    correlation_id,
                ),
            )
            connection.commit()
        return {
            "incident_id": incident_id,
            "previous_status": current_status,
            "status": requested_status,
            "result": "completed",
        }

    def get_audit(self, incident_id: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT sequence, action, actor_role, at, result, correlation_id "
                "FROM incident_audit WHERE incident_id=? ORDER BY sequence",
                (incident_id,),
            ).fetchall()
        return [dict(row) for row in rows]
