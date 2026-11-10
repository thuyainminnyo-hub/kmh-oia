"""Durable local SQLite store for KMH signing-key registry snapshots.

The hash-chained event ledger is tamper-evident only relative to a separately
retained checkpoint. It is not an independently witnessed transparency log.
SQLite WAL databases must remain on a local filesystem, not a network share.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import rfc8785

from scripts.preservation_ingest import (
    IntakeError,
    KEY_REGISTRY_SCHEMA,
    _validate_signing_key_registry_entry,
)

STORE_SCHEMA_VERSION = 1
GENESIS_HASH = "0" * 64


def _canonical(value: Any) -> bytes:
    try:
        return rfc8785.dumps(value)
    except Exception as exc:
        raise IntakeError("INVALID_CANONICAL_JSON", "Registry data is not RFC 8785 canonicalizable") from exc


def _event_hash(previous_hash: str, event: dict) -> str:
    payload = _canonical(event)
    return hashlib.sha256(b"KMH-KEY-AUDIT-v1\x00" + bytes.fromhex(previous_hash) + payload).hexdigest()


class SQLiteSigningKeyRegistryStore:
    """Single-host durable registry with atomic versioned commits and hash-chained events."""

    def __init__(self, database_path: str | Path, *, busy_timeout_ms: int = 5000):
        self.database_path = str(database_path)
        self.busy_timeout_ms = busy_timeout_ms
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute(f"PRAGMA busy_timeout={int(self.busy_timeout_ms)}")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            if self.database_path != ":memory:":
                connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS registry_meta (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    schema_version INTEGER NOT NULL,
                    registry_version INTEGER NOT NULL,
                    latest_event_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS signing_keys (
                    key_id TEXT PRIMARY KEY,
                    entry_json BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS key_audit_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_json BLOB NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                );
            """)
            connection.execute(
                """INSERT OR IGNORE INTO registry_meta
                   (singleton, schema_version, registry_version, latest_event_hash)
                   VALUES (1, ?, 0, ?)""",
                (STORE_SCHEMA_VERSION, GENESIS_HASH),
            )
            row = connection.execute(
                "SELECT schema_version FROM registry_meta WHERE singleton=1"
            ).fetchone()
            if row is None or row["schema_version"] != STORE_SCHEMA_VERSION:
                raise IntakeError("UNSUPPORTED_KEY_STORE_SCHEMA", "Unsupported durable key registry schema")

    def load_registry(self) -> tuple[dict, int]:
        with self._connect() as connection:
            meta = connection.execute(
                "SELECT registry_version FROM registry_meta WHERE singleton=1"
            ).fetchone()
            keys = {}
            for row in connection.execute("SELECT key_id, entry_json FROM signing_keys ORDER BY key_id"):
                keys[row["key_id"]] = json.loads(bytes(row["entry_json"]).decode("utf-8"))
            events = [
                json.loads(bytes(row["event_json"]).decode("utf-8"))
                for row in connection.execute("SELECT event_json FROM key_audit_events ORDER BY sequence")
            ]
            return {
                "schema": KEY_REGISTRY_SCHEMA,
                "version": 1,
                "keys": keys,
                "events": events,
            }, int(meta["registry_version"])

    def commit_registry(self, registry: dict, *, expected_version: int) -> int:
        if not isinstance(registry, dict) or registry.get("schema") != KEY_REGISTRY_SCHEMA or registry.get("version") != 1:
            raise IntakeError("INVALID_KEY_REGISTRY", "Unsupported signing key registry")
        if not isinstance(registry.get("keys"), dict) or not isinstance(registry.get("events"), list):
            raise IntakeError("INVALID_KEY_REGISTRY", "Registry keys and events must be collections")
        for key_id, entry in registry["keys"].items():
            if key_id != entry.get("key_id"):
                raise IntakeError("INVALID_KEY_REGISTRY", "Key map index does not match key ID")
            _validate_signing_key_registry_entry(entry)

        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                meta = connection.execute(
                    "SELECT registry_version, latest_event_hash FROM registry_meta WHERE singleton=1"
                ).fetchone()
                actual_version = int(meta["registry_version"])
                if actual_version != expected_version:
                    raise IntakeError("KEY_REGISTRY_VERSION_CONFLICT", "Registry changed since it was loaded")
                existing_events = [
                    json.loads(bytes(row["event_json"]).decode("utf-8"))
                    for row in connection.execute("SELECT event_json FROM key_audit_events ORDER BY sequence")
                ]
                if registry["events"][:len(existing_events)] != existing_events:
                    raise IntakeError("KEY_AUDIT_HISTORY_REWRITE", "Existing key audit events cannot be rewritten or removed")
                appended_events = registry["events"][len(existing_events):]
                previous_hash = meta["latest_event_hash"]
                for event in appended_events:
                    if not isinstance(event, dict):
                        raise IntakeError("INVALID_KEY_AUDIT_EVENT", "Audit event must be an object")
                    event_bytes = _canonical(event)
                    digest = _event_hash(previous_hash, event)
                    connection.execute(
                        "INSERT INTO key_audit_events(event_json, previous_hash, event_hash) VALUES (?, ?, ?)",
                        (event_bytes, previous_hash, digest),
                    )
                    previous_hash = digest

                current_rows = {
                    row["key_id"]: json.loads(bytes(row["entry_json"]).decode("utf-8"))
                    for row in connection.execute("SELECT key_id, entry_json FROM signing_keys")
                }
                for key_id, old_entry in current_rows.items():
                    new_entry = registry["keys"].get(key_id)
                    if new_entry is None:
                        raise IntakeError("KEY_REGISTRY_DELETE_FORBIDDEN", "Registered keys cannot be deleted")
                    immutable = ("schema", "key_id", "algorithm", "public_key_b64", "public_key_sha256", "created_at", "activate_at", "signing_not_after")
                    if any(old_entry.get(field) != new_entry.get(field) for field in immutable):
                        raise IntakeError("KEY_REGISTRY_IDENTITY_REWRITE", "Key identity fields are immutable")
                    old_history = old_entry.get("state_history", [])
                    new_history = new_entry.get("state_history", [])
                    if new_history[:len(old_history)] != old_history:
                        raise IntakeError("KEY_STATE_HISTORY_REWRITE", "Existing key state history cannot be rewritten")
                    if len(new_history) < len(old_history):
                        raise IntakeError("KEY_STATE_HISTORY_REWRITE", "Key state history cannot shrink")

                for key_id, entry in registry["keys"].items():
                    connection.execute(
                        """INSERT INTO signing_keys(key_id, entry_json) VALUES (?, ?)
                           ON CONFLICT(key_id) DO UPDATE SET entry_json=excluded.entry_json""",
                        (key_id, _canonical(entry)),
                    )
                connection.execute(
                    """UPDATE registry_meta
                       SET registry_version=?, latest_event_hash=?
                       WHERE singleton=1""",
                    (actual_version + 1, previous_hash),
                )
                connection.execute("COMMIT")
                return actual_version + 1
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def verify_audit_chain(self) -> dict:
        with self._connect() as connection:
            previous_hash = GENESIS_HASH
            count = 0
            for row in connection.execute(
                "SELECT event_json, previous_hash, event_hash FROM key_audit_events ORDER BY sequence"
            ):
                event = json.loads(bytes(row["event_json"]).decode("utf-8"))
                if row["previous_hash"] != previous_hash:
                    return {"valid": False, "events_verified": count, "reason": "previous_hash_mismatch"}
                expected = _event_hash(previous_hash, event)
                if row["event_hash"] != expected:
                    return {"valid": False, "events_verified": count, "reason": "event_hash_mismatch"}
                previous_hash = expected
                count += 1
            meta = connection.execute(
                "SELECT latest_event_hash FROM registry_meta WHERE singleton=1"
            ).fetchone()
            if meta["latest_event_hash"] != previous_hash:
                return {"valid": False, "events_verified": count, "reason": "checkpoint_mismatch"}
            return {"valid": True, "events_verified": count, "latest_event_hash": previous_hash}
