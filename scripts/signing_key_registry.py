"""Durable SQLite signing-key registry with transactional lifecycle and hash-chained audit.

This is a local durable-store prototype, not a tamper-proof remote trust service.
The database owner can still replace the database or disable triggers; production
deployment needs independent audit witnessing and managed key custody.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import rfc8785

from scripts.preservation_ingest import (
    IntakeError,
    KEY_REGISTRY_SCHEMA,
    KEY_STATES,
    KEY_TRANSITIONS,
    KEY_ENTRY_SCHEMA,
    _parse_aware_time,
    _validate_signing_key_registry_entry,
    _registry_entry_eligible_for_signing,
)

DB_SCHEMA_VERSION = 1
GENESIS_HASH = "0" * 64


def _canonical(value: object) -> bytes:
    try:
        return rfc8785.dumps(value)
    except Exception as exc:
        raise IntakeError("INVALID_REGISTRY_EVENT", "Registry event is not valid RFC 8785 JSON") from exc


def _utc(value: str) -> str:
    return _parse_aware_time(value).isoformat()


class DurableSigningKeyRegistry:
    """SQLite-backed registry; each mutation commits key state and audit atomically."""

    def __init__(self, database_path: str | Path, *, busy_timeout_ms: int = 5000):
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self.busy_timeout_ms = busy_timeout_ms
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(f"PRAGMA busy_timeout={int(self.busy_timeout_ms)}")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        connection = self._connect()
        try:
            if self.database_path != ":memory:":
                connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS registry_meta (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    schema_version INTEGER NOT NULL,
                    registry_schema TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS signing_keys (
                    key_id TEXT PRIMARY KEY,
                    entry_json TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('pre_active','active','retired','compromised','revoked')),
                    public_key_sha256 TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS key_audit_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_json TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                );
                CREATE TRIGGER IF NOT EXISTS key_audit_no_update
                BEFORE UPDATE ON key_audit_events
                BEGIN SELECT RAISE(ABORT, 'key audit events are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS key_audit_no_delete
                BEFORE DELETE ON key_audit_events
                BEGIN SELECT RAISE(ABORT, 'key audit events are append-only'); END;
            """)
            row = connection.execute("SELECT schema_version, registry_schema FROM registry_meta WHERE singleton=1").fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO registry_meta(singleton,schema_version,registry_schema) VALUES(1,?,?)",
                    (DB_SCHEMA_VERSION, KEY_REGISTRY_SCHEMA),
                )
            elif row["schema_version"] != DB_SCHEMA_VERSION or row["registry_schema"] != KEY_REGISTRY_SCHEMA:
                raise IntakeError("UNSUPPORTED_REGISTRY_DATABASE", "Registry database schema version is unsupported")
        finally:
            connection.close()

    def _entry(self, connection: sqlite3.Connection, key_id: str) -> dict:
        row = connection.execute("SELECT entry_json FROM signing_keys WHERE key_id=?", (key_id,)).fetchone()
        if row is None:
            raise IntakeError("SIGNING_KEY_NOT_FOUND", "Signing key is not registered")
        return json.loads(row["entry_json"])

    def _save_entry(self, connection: sqlite3.Connection, entry: dict) -> None:
        _validate_signing_key_registry_entry(entry)
        connection.execute(
            """INSERT INTO signing_keys(key_id,entry_json,state,public_key_sha256)
               VALUES(?,?,?,?)
               ON CONFLICT(key_id) DO UPDATE SET
                 entry_json=excluded.entry_json,
                 state=excluded.state,
                 public_key_sha256=excluded.public_key_sha256""",
            (
                entry["key_id"],
                _canonical(entry).decode("utf-8"),
                entry["state"],
                entry["public_key_sha256"],
            ),
        )

    def _append_event(
        self, connection: sqlite3.Connection, event_type: str, key_id: str,
        at: str, data: dict,
    ) -> None:
        previous = connection.execute(
            "SELECT event_hash FROM key_audit_events ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        previous_hash = previous["event_hash"] if previous else GENESIS_HASH
        event = {
            "event_type": event_type,
            "key_id": key_id,
            "at": _utc(at),
            "data": data,
        }
        event_bytes = _canonical(event)
        event_hash = hashlib.sha256(bytes.fromhex(previous_hash) + event_bytes).hexdigest()
        connection.execute(
            "INSERT INTO key_audit_events(event_json,previous_hash,event_hash) VALUES(?,?,?)",
            (event_bytes.decode("utf-8"), previous_hash, event_hash),
        )

    def register(self, entry: dict) -> None:
        _validate_signing_key_registry_entry(entry)
        with self._transaction() as connection:
            exists = connection.execute("SELECT 1 FROM signing_keys WHERE key_id=?", (entry["key_id"],)).fetchone()
            if exists:
                raise IntakeError("DUPLICATE_SIGNING_KEY_ID", "Signing key ID is already registered")
            self._save_entry(connection, entry)
            self._append_event(
                connection, "key_registered", entry["key_id"], entry["created_at"],
                {"public_key_sha256": entry["public_key_sha256"], "state": entry["state"]},
            )

    def transition(
        self, key_id: str, *, target_state: str, at: str, reason: str,
        replacement_key_id: str | None = None,
    ) -> dict:
        with self._transaction() as connection:
            current = self._entry(connection, key_id)
            transitioned_at = _parse_aware_time(at)
            if transitioned_at < _parse_aware_time(current["state_changed_at"]):
                raise IntakeError("INVALID_KEY_TIME", "Key lifecycle time cannot move backwards")
            if target_state not in KEY_TRANSITIONS.get(current["state"], set()):
                raise IntakeError("INVALID_KEY_STATE_TRANSITION", "Requested key lifecycle transition is not allowed")
            if target_state in {"retired", "compromised", "revoked"} and (not isinstance(reason, str) or not reason.strip()):
                raise IntakeError("KEY_STATE_REASON_REQUIRED", "A reason is required for this lifecycle transition")
            if target_state == "active":
                if transitioned_at < _parse_aware_time(current["activate_at"]):
                    raise IntakeError("KEY_NOT_YET_ACTIVATABLE", "Key cannot become active before its activation time")
                if current.get("signing_not_after") and transitioned_at >= _parse_aware_time(current["signing_not_after"]):
                    raise IntakeError("SIGNING_KEY_EXPIRED", "Key cannot be activated after its signing period")
            if target_state == "retired":
                if not replacement_key_id or replacement_key_id == key_id:
                    raise IntakeError("REPLACEMENT_KEY_REQUIRED", "Retirement requires an active replacement key")
                replacement = self._entry(connection, replacement_key_id)
                if replacement["state"] != "active":
                    raise IntakeError("REPLACEMENT_KEY_NOT_ACTIVE", "Replacement key must be active before retirement")
            updated = dict(current)
            updated["state"] = target_state
            updated["state_changed_at"] = transitioned_at.isoformat()
            updated["reason"] = reason.strip() if isinstance(reason, str) else ""
            updated["replacement_key_id"] = replacement_key_id
            history = list(current.get("state_history", []))
            history.append({
                "state": target_state, "at": transitioned_at.isoformat(),
                "reason": updated["reason"], "replacement_key_id": replacement_key_id,
            })
            updated["state_history"] = history
            self._save_entry(connection, updated)
            self._append_event(
                connection, "key_state_changed", key_id, at,
                {"from": current["state"], "to": target_state, "reason": updated["reason"],
                 "replacement_key_id": replacement_key_id,
                 "public_key_sha256": updated["public_key_sha256"]},
            )
            return updated

    def rotate(self, old_key_id: str, replacement_entry: dict, *, at: str, reason: str) -> None:
        """Register, activate replacement and retire old key in one SQLite transaction."""
        _validate_signing_key_registry_entry(replacement_entry)
        with self._transaction() as connection:
            old = self._entry(connection, old_key_id)
            if old["state"] != "active":
                raise IntakeError("KEY_NOT_ACTIVE", "Only an active key can be normally rotated")
            if connection.execute("SELECT 1 FROM signing_keys WHERE key_id=?", (replacement_entry["key_id"],)).fetchone():
                raise IntakeError("DUPLICATE_SIGNING_KEY_ID", "Replacement key ID already exists")
            self._save_entry(connection, replacement_entry)
            self._append_event(connection, "key_registered", replacement_entry["key_id"], replacement_entry["created_at"],
                               {"public_key_sha256": replacement_entry["public_key_sha256"], "state": "pre_active"})
            new_entry = dict(replacement_entry)
            activation = _parse_aware_time(at)
            if activation < _parse_aware_time(new_entry["activate_at"]):
                raise IntakeError("KEY_NOT_YET_ACTIVATABLE", "Replacement key activation time has not arrived")
            if new_entry.get("signing_not_after") and activation >= _parse_aware_time(new_entry["signing_not_after"]):
                raise IntakeError("SIGNING_KEY_EXPIRED", "Replacement key signing period has ended")
            new_entry["state"] = "active"
            new_entry["state_changed_at"] = activation.isoformat()
            new_entry["reason"] = "activated for key rotation"
            new_entry["state_history"] = list(new_entry.get("state_history", [])) + [{
                "state": "active", "at": activation.isoformat(), "reason": new_entry["reason"],
                "replacement_key_id": None,
            }]
            self._save_entry(connection, new_entry)
            self._append_event(connection, "key_activated", new_entry["key_id"], at,
                               {"reason": new_entry["reason"], "public_key_sha256": new_entry["public_key_sha256"]})
            old_updated = dict(old)
            old_updated["state"] = "retired"
            old_updated["state_changed_at"] = activation.isoformat()
            old_updated["reason"] = reason.strip()
            old_updated["replacement_key_id"] = new_entry["key_id"]
            old_updated["state_history"] = list(old.get("state_history", [])) + [{
                "state": "retired", "at": activation.isoformat(), "reason": reason.strip(),
                "replacement_key_id": new_entry["key_id"],
            }]
            self._save_entry(connection, old_updated)
            self._append_event(connection, "key_retired", old_key_id, at,
                               {"reason": reason.strip(), "replacement_key_id": new_entry["key_id"],
                                "public_key_sha256": old["public_key_sha256"]})
            self._append_event(connection, "key_rotation_completed", old_key_id, at,
                               {"old_key_id": old_key_id, "new_key_id": new_entry["key_id"]})

    def compromise(self, key_id: str, *, at: str, reason: str) -> dict:
        return self.transition(key_id, target_state="compromised", at=at, reason=reason)

    def get_entry(self, key_id: str) -> dict:
        connection = self._connect()
        try:
            return self._entry(connection, key_id)
        finally:
            connection.close()

    def public_keys_for_execution(self) -> dict:
        """Return active, currently eligible Ed25519 public keys for new approvals."""
        connection = self._connect()
        try:
            rows = connection.execute("SELECT entry_json FROM signing_keys WHERE state='active'").fetchall()
            result = {}
            for row in rows:
                entry = json.loads(row["entry_json"])
                public_key = _registry_entry_eligible_for_signing(entry, entry["state_changed_at"])
                result[entry["key_id"]] = public_key
            return result
        finally:
            connection.close()

    def audit_events(self) -> list[dict]:
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT sequence,event_json,previous_hash,event_hash FROM key_audit_events ORDER BY sequence"
            ).fetchall()
            return [{
                "sequence": row["sequence"], "event": json.loads(row["event_json"]),
                "previous_hash": row["previous_hash"], "event_hash": row["event_hash"],
            } for row in rows]
        finally:
            connection.close()

    def verify_audit_chain(self) -> bool:
        previous_hash = GENESIS_HASH
        for item in self.audit_events():
            event_bytes = _canonical(item["event"])
            if item["previous_hash"] != previous_hash:
                return False
            calculated = hashlib.sha256(bytes.fromhex(previous_hash) + event_bytes).hexdigest()
            if calculated != item["event_hash"]:
                return False
            previous_hash = calculated
        return True

    def close(self) -> None:
        """Connections are scoped per operation; present for context-manager symmetry."""
        return None

    def __enter__(self) -> "DurableSigningKeyRegistry":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
