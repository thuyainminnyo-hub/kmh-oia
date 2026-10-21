"""SQLite-backed atomic persistence boundary for governed learning admissions.

TrustedDecisionLearningService uses this repository for atomic admission,
learning-record, optional proposal, and audit writes. Durability is local to the
configured filesystem database; this module does not claim shared multi-host
transactions or production deployment by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from pathlib import Path
from typing import Any, Callable


class AdmissionConflictError(ValueError):
    """Raised if an idempotency key is reused with different request content."""


@dataclass(frozen=True)
class AdmissionCommit:
    admission_key: str
    fingerprint: str
    learning_record: dict[str, Any]
    adaptation_proposal: dict[str, Any] | None
    audit_event: dict[str, Any]
    result: dict[str, Any]


class SQLiteLearningAdmissionRepository:
    """Atomically persist one learning admission and its related effects."""

    def __init__(self, database_path: str | Path, *, timeout: float = 5.0) -> None:
        path = str(database_path)
        if not path.strip() or path == ":memory:":
            raise ValueError("A durable filesystem database path is required.")
        self.database_path = Path(path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                PRAGMA foreign_keys=ON;
                CREATE TABLE IF NOT EXISTS learning_admissions (
                    admission_key TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('COMPLETED')),
                    result_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS learning_records (
                    admission_key TEXT PRIMARY KEY REFERENCES learning_admissions(admission_key),
                    command_id TEXT NOT NULL,
                    record_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS adaptation_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    admission_key TEXT NOT NULL UNIQUE REFERENCES learning_admissions(admission_key),
                    proposal_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS admission_audit_events (
                    event_id TEXT PRIMARY KEY,
                    admission_key TEXT NOT NULL REFERENCES learning_admissions(admission_key),
                    event_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_learning_records_command_id
                    ON learning_records(command_id);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.database_path),
            timeout=self.timeout,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(f"PRAGMA busy_timeout={int(self.timeout * 1000)}")
        return connection

    @staticmethod
    def _canonical(value: dict[str, Any]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def get(self, admission_key: str) -> AdmissionCommit | None:
        if not admission_key.strip():
            raise ValueError("admission_key is required")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT fingerprint, result_json FROM learning_admissions "
                "WHERE admission_key = ? AND status = 'COMPLETED'",
                (admission_key.strip(),),
            ).fetchone()
            if row is None:
                return None
            record = connection.execute(
                "SELECT record_json FROM learning_records WHERE admission_key = ?",
                (admission_key.strip(),),
            ).fetchone()
            proposal = connection.execute(
                "SELECT proposal_json FROM adaptation_proposals WHERE admission_key = ?",
                (admission_key.strip(),),
            ).fetchone()
            audit = connection.execute(
                "SELECT event_json FROM admission_audit_events WHERE admission_key = ? "
                "ORDER BY event_id DESC LIMIT 1",
                (admission_key.strip(),),
            ).fetchone()
            if record is None or audit is None:
                raise RuntimeError("Completed admission is missing required persisted records.")
            return AdmissionCommit(
                admission_key=admission_key.strip(),
                fingerprint=row["fingerprint"],
                learning_record=json.loads(record["record_json"]),
                adaptation_proposal=json.loads(proposal["proposal_json"]) if proposal else None,
                audit_event=json.loads(audit["event_json"]),
                result=json.loads(row["result_json"]),
            )

    def commit(
        self,
        *,
        admission_key: str,
        fingerprint: str,
        learning_record: dict[str, Any],
        adaptation_proposal: dict[str, Any] | None,
        audit_event: dict[str, Any],
        result: dict[str, Any],
        before_commit: Callable[[str], None] | None = None,
    ) -> AdmissionCommit:
        """Persist all effects atomically, or return the stored result on retry.

        before_commit is a failure-injection test seam, never for external effects.
        """
        key = admission_key.strip() if isinstance(admission_key, str) else ""
        fp = fingerprint.strip() if isinstance(fingerprint, str) else ""
        if not key:
            raise ValueError("admission_key is required")
        if not fp:
            raise ValueError("fingerprint is required")
        if not isinstance(learning_record, dict) or not learning_record:
            raise ValueError("learning_record must be a non-empty object")
        if not isinstance(audit_event, dict) or not audit_event:
            raise ValueError("audit_event must be a non-empty object")
        if not isinstance(result, dict):
            raise ValueError("result must be an object")
        command_id = learning_record.get("command_id")
        if not isinstance(command_id, str) or not command_id.strip():
            raise ValueError("learning_record.command_id is required")
        proposal_id = None
        if adaptation_proposal is not None:
            proposal_id = adaptation_proposal.get("id")
            if not isinstance(proposal_id, str) or not proposal_id.strip():
                raise ValueError("adaptation_proposal.id is required")
            if adaptation_proposal.get("status", "PROPOSED") != "PROPOSED":
                raise ValueError("new adaptation proposals must start in PROPOSED status")
        event_id = audit_event.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("audit_event.event_id is required")
        if audit_event.get("admission_key", key) != key:
            raise ValueError("audit_event.admission_key must match admission_key")

        stored_result = self._canonical(result)
        stored_record = self._canonical(learning_record)
        stored_audit = self._canonical({**audit_event, "admission_key": key})
        stored_proposal = self._canonical(adaptation_proposal) if adaptation_proposal is not None else None

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                existing = connection.execute(
                    "SELECT fingerprint, status FROM learning_admissions WHERE admission_key = ?",
                    (key,),
                ).fetchone()
                if existing is not None:
                    if existing["fingerprint"] != fp:
                        raise AdmissionConflictError(
                            "Idempotency key already exists with a different request fingerprint."
                        )
                    if existing["status"] == "COMPLETED":
                        connection.execute("COMMIT")
                        saved = self.get(key)
                        if saved is None:
                            raise RuntimeError("Completed admission could not be read back.")
                        return saved
                    raise RuntimeError("Admission has an unsupported persisted state.")

                connection.execute(
                    "INSERT INTO learning_admissions(admission_key, fingerprint, status, result_json) "
                    "VALUES (?, ?, 'COMPLETED', ?)",
                    (key, fp, stored_result),
                )
                if before_commit:
                    before_commit("admission")
                connection.execute(
                    "INSERT INTO learning_records(admission_key, command_id, record_json) VALUES (?, ?, ?)",
                    (key, command_id.strip(), stored_record),
                )
                if before_commit:
                    before_commit("learning_record")
                if adaptation_proposal is not None:
                    connection.execute(
                        "INSERT INTO adaptation_proposals(proposal_id, admission_key, proposal_json) "
                        "VALUES (?, ?, ?)",
                        (proposal_id.strip(), key, stored_proposal),
                    )
                if before_commit:
                    before_commit("adaptation_proposal")
                connection.execute(
                    "INSERT INTO admission_audit_events(event_id, admission_key, event_json) "
                    "VALUES (?, ?, ?)",
                    (event_id.strip(), key, stored_audit),
                )
                if before_commit:
                    before_commit("audit_event")
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

        saved = self.get(key)
        if saved is None:
            raise RuntimeError("Committed admission could not be read back.")
        return saved

    def counts(self) -> dict[str, int]:
        with self._connect() as connection:
            return {
                table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in (
                    "learning_admissions",
                    "learning_records",
                    "adaptation_proposals",
                    "admission_audit_events",
                )
            }
