"""Receipt replay/idempotency stores for trusted evidence admission.

The SQLite implementation is durable across process restarts and uses a
unique primary key to make receipt claims atomic across processes sharing the
same database file. For multi-host production, use a shared transactional store
with equivalent unique-key/atomic-insert semantics.
"""
from dataclasses import dataclass
import sqlite3
from threading import Lock
from typing import Protocol


@dataclass(frozen=True)
class ReplayClaim:
    accepted: bool
    key: str
    reason: str


class ReceiptReplayStore(Protocol):
    def claim(self, provider_name: str, source_record_id: str, content_hash: str) -> ReplayClaim: ...


def _make_key(provider_name: str, source_record_id: str, content_hash: str) -> tuple[str, str]:
    parts = tuple(value.strip() if isinstance(value, str) else "" for value in (
        provider_name, source_record_id, content_hash
    ))
    if not all(parts):
        return "", ""
    # Length-prefix to avoid ambiguous collisions if values contain separators.
    key = "".join(f"{len(value)}:{value}" for value in parts)
    return key, "|".join(parts)


class InMemoryReceiptReplayStore:
    """Thread-safe process-local implementation for development and tests."""

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._lock = Lock()

    def claim(self, provider_name: str, source_record_id: str, content_hash: str) -> ReplayClaim:
        key, display_key = _make_key(provider_name, source_record_id, content_hash)
        if not key:
            return ReplayClaim(False, "", "Replay key fields are required.")
        with self._lock:
            if key in self._seen:
                return ReplayClaim(False, display_key, "Receipt replay detected.")
            self._seen.add(key)
        return ReplayClaim(True, display_key, "Receipt replay key claimed.")


class SQLiteReceiptReplayStore:
    """Durable replay guard for local/single-host runtimes."""

    def __init__(self, path: str) -> None:
        from pathlib import Path

        if not isinstance(path, str) or not path.strip():
            raise ValueError("SQLite replay store path must be a non-empty file path")
        self.path = path
        target = Path(path)
        if str(path) != ":memory:":
            target.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS receipt_replay_claims (
                    replay_key TEXT PRIMARY KEY,
                    provider_name TEXT NOT NULL,
                    source_record_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    claimed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def health_check(self) -> bool:
        """Return whether the store can read its schema and database."""
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    ("receipt_replay_claims",),
                ).fetchone()
            return row is not None
        except sqlite3.Error:
            return False

    def claim(self, provider_name: str, source_record_id: str, content_hash: str) -> ReplayClaim:
        key, display_key = _make_key(provider_name, source_record_id, content_hash)
        if not key:
            return ReplayClaim(False, "", "Replay key fields are required.")
        parts = tuple(value.strip() for value in (provider_name, source_record_id, content_hash))
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO receipt_replay_claims
                        (replay_key, provider_name, source_record_id, content_hash)
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, *parts),
                )
        except sqlite3.IntegrityError:
            return ReplayClaim(False, display_key, "Receipt replay detected.")
        except sqlite3.Error:
            return ReplayClaim(False, display_key, "Replay store unavailable; admission blocked.")
        return ReplayClaim(True, display_key, "Receipt replay key claimed durably.")
