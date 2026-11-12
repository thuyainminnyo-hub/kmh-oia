"""Linked caller/serving-party evidence prototype.

Both sides independently commit to one call. This is local application logic,
not a wire-compatible SCITT implementation or cryptographic trust boundary.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from threading import RLock
from dataclasses import asdict, dataclass
from typing import Any


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class CallerEvidence:
    request_id: str
    caller_agent_id: str
    caller_receipt_digest: str
    call_digest: str


@dataclass(frozen=True)
class ServingAdmissionReceipt:
    sequence: int
    serving_party_id: str
    request_id: str
    caller_agent_id: str
    caller_receipt_digest: str
    call_digest: str
    decision: str
    reason_code: str
    occurred_at_epoch: int
    previous_receipt_digest: str


@dataclass(frozen=True)
class LinkedEvidence:
    caller_receipt_digest: str
    admission_receipt_digest: str
    call_digest: str
    request_id: str


class ReplayDetected(ValueError):
    pass


class ServingEvidenceLedger:
    """In-memory admission ledger; persistence and distributed replay are TODO."""

    _GENESIS = "0" * 64

    def __init__(self, serving_party_id: str) -> None:
        if not serving_party_id.strip():
            raise ValueError("serving_party_id is required")
        self.serving_party_id = serving_party_id
        self._receipts: list[ServingAdmissionReceipt] = []
        self._seen_caller_refs: set[tuple[str, str]] = set()

    @property
    def receipts(self) -> tuple[ServingAdmissionReceipt, ...]:
        return tuple(self._receipts)

    def admit(
        self,
        *,
        caller: CallerEvidence,
        actual_request: dict[str, Any],
        decision: str,
        reason_code: str,
        occurred_at_epoch: int,
    ) -> ServingAdmissionReceipt:
        if decision not in {"allow", "deny", "indeterminate"}:
            raise ValueError("invalid admission decision")
        if not caller.request_id.strip() or not caller.caller_agent_id.strip():
            raise ValueError("caller identity and request ID are required")
        if not reason_code.strip() or occurred_at_epoch < 0:
            raise ValueError("reason code and valid timestamp are required")
        computed = _digest(_canonical(actual_request))
        if computed != caller.call_digest:
            raise ValueError("caller call digest does not match serving-party request digest")
        replay_key = (caller.caller_agent_id, caller.caller_receipt_digest)
        if replay_key in self._seen_caller_refs:
            raise ReplayDetected("caller receipt reference already admitted")
        sequence = len(self._receipts) + 1
        previous = self._GENESIS if not self._receipts else _digest(_canonical(self._receipts[-1].__dict__))
        receipt = ServingAdmissionReceipt(
            sequence=sequence,
            serving_party_id=self.serving_party_id,
            request_id=caller.request_id,
            caller_agent_id=caller.caller_agent_id,
            caller_receipt_digest=caller.caller_receipt_digest,
            call_digest=computed,
            decision=decision,
            reason_code=reason_code,
            occurred_at_epoch=occurred_at_epoch,
            previous_receipt_digest=previous,
        )
        self._receipts.append(receipt)
        self._seen_caller_refs.add(replay_key)
        return receipt

    def verify_chain(self) -> bool:
        previous = self._GENESIS
        seen: set[tuple[str, str]] = set()
        for expected_sequence, receipt in enumerate(self._receipts, start=1):
            if receipt.sequence != expected_sequence:
                return False
            if receipt.serving_party_id != self.serving_party_id:
                return False
            if receipt.previous_receipt_digest != previous:
                return False
            key = (receipt.caller_agent_id, receipt.caller_receipt_digest)
            if key in seen:
                return False
            seen.add(key)
            previous = _digest(_canonical(receipt.__dict__))
        return True


def link_caller_and_admission(
    *,
    caller: CallerEvidence,
    admission: ServingAdmissionReceipt,
    actual_request: dict[str, Any],
) -> LinkedEvidence | None:
    """Verify both parties refer to the same request and caller receipt."""
    computed = _digest(_canonical(actual_request))
    if caller.request_id != admission.request_id:
        return None
    if caller.caller_agent_id != admission.caller_agent_id:
        return None
    if caller.caller_receipt_digest != admission.caller_receipt_digest:
        return None
    if caller.call_digest != computed or admission.call_digest != computed:
        return None
    if admission.decision not in {"allow", "deny", "indeterminate"}:
        return None
    return LinkedEvidence(
        caller_receipt_digest=caller.caller_receipt_digest,
        admission_receipt_digest=_digest(_canonical(admission.__dict__)),
        call_digest=computed,
        request_id=caller.request_id,
    )



class SQLiteServingEvidenceLedger:
    """Persistent serving-party ledger with transactional per-caller replay protection.

    Local SQLite durability only: this is not a remote SCITT Transparency Service,
    WORM store, or protection against a privileged database administrator.
    """

    _GENESIS = "0" * 64

    def __init__(self, database_path: str | Path, serving_party_id: str) -> None:
        if not isinstance(serving_party_id, str) or not serving_party_id.strip():
            raise ValueError("serving_party_id is required")
        self.database_path = str(database_path)
        self.serving_party_id = serving_party_id
        self._lock = RLock()
        self._db = sqlite3.connect(
            self.database_path, check_same_thread=False, isolation_level=None,
            timeout=30,
        )
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS serving_receipts (
                sequence INTEGER PRIMARY KEY,
                serving_party_id TEXT NOT NULL,
                request_id TEXT NOT NULL,
                caller_agent_id TEXT NOT NULL,
                caller_receipt_digest TEXT NOT NULL,
                call_digest TEXT NOT NULL,
                decision TEXT NOT NULL,
                reason_code TEXT NOT NULL,
                occurred_at_epoch INTEGER NOT NULL,
                previous_receipt_digest TEXT NOT NULL,
                receipt_digest TEXT NOT NULL UNIQUE,
                UNIQUE(serving_party_id, caller_agent_id, caller_receipt_digest)
            );
            CREATE TRIGGER IF NOT EXISTS serving_receipts_no_update
            BEFORE UPDATE ON serving_receipts
            BEGIN SELECT RAISE(ABORT, 'serving receipts are append-only'); END;
            CREATE TRIGGER IF NOT EXISTS serving_receipts_no_delete
            BEFORE DELETE ON serving_receipts
            BEGIN SELECT RAISE(ABORT, 'serving receipts are append-only'); END;
        """)

    def admit(
        self, *, caller: CallerEvidence, actual_request: dict[str, Any],
        decision: str, reason_code: str, occurred_at_epoch: int,
    ) -> ServingAdmissionReceipt:
        if decision not in {"allow", "deny", "indeterminate"}:
            raise ValueError("invalid admission decision")
        if not all(isinstance(v, str) and v.strip() for v in (
            caller.request_id, caller.caller_agent_id, caller.caller_receipt_digest,
            caller.call_digest, reason_code,
        )):
            raise ValueError("required caller evidence fields are missing")
        for label, value in (
            ("caller_receipt_digest", caller.caller_receipt_digest),
            ("call_digest", caller.call_digest),
        ):
            if len(value) != 64:
                raise ValueError(f"{label} must be a SHA-256 hex digest")
            try:
                int(value, 16)
            except ValueError as exc:
                raise ValueError(f"{label} must be a SHA-256 hex digest") from exc
        if not isinstance(occurred_at_epoch, int) or occurred_at_epoch < 0:
            raise ValueError("invalid timestamp")
        computed = _digest(_canonical(actual_request))
        if computed != caller.call_digest:
            raise ValueError("caller call digest does not match serving-party request digest")
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                row = self._db.execute(
                    "SELECT sequence, receipt_digest FROM serving_receipts "
                    "WHERE serving_party_id=? ORDER BY sequence DESC LIMIT 1",
                    (self.serving_party_id,),
                ).fetchone()
                sequence = 1 if row is None else int(row["sequence"]) + 1
                previous = self._GENESIS if row is None else str(row["receipt_digest"])
                receipt = ServingAdmissionReceipt(
                    sequence=sequence, serving_party_id=self.serving_party_id,
                    request_id=caller.request_id, caller_agent_id=caller.caller_agent_id,
                    caller_receipt_digest=caller.caller_receipt_digest,
                    call_digest=computed, decision=decision, reason_code=reason_code,
                    occurred_at_epoch=occurred_at_epoch,
                    previous_receipt_digest=previous,
                )
                digest = _digest(_canonical(asdict(receipt)))
                self._db.execute(
                    """INSERT INTO serving_receipts
                    (sequence, serving_party_id, request_id, caller_agent_id,
                     caller_receipt_digest, call_digest, decision, reason_code,
                     occurred_at_epoch, previous_receipt_digest, receipt_digest)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (receipt.sequence, receipt.serving_party_id, receipt.request_id,
                     receipt.caller_agent_id, receipt.caller_receipt_digest,
                     receipt.call_digest, receipt.decision, receipt.reason_code,
                     receipt.occurred_at_epoch, receipt.previous_receipt_digest, digest),
                )
                self._db.execute("COMMIT")
                return receipt
            except sqlite3.IntegrityError as exc:
                self._db.execute("ROLLBACK")
                if "UNIQUE constraint failed" in str(exc):
                    raise ReplayDetected("caller receipt reference already admitted") from exc
                raise
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    @property
    def receipts(self) -> tuple[ServingAdmissionReceipt, ...]:
        with self._lock:
            rows = self._db.execute(
                """SELECT sequence, serving_party_id, request_id, caller_agent_id,
                   caller_receipt_digest, call_digest, decision, reason_code,
                   occurred_at_epoch, previous_receipt_digest
                   FROM serving_receipts WHERE serving_party_id=? ORDER BY sequence""",
                (self.serving_party_id,),
            ).fetchall()
            return tuple(ServingAdmissionReceipt(**dict(row)) for row in rows)

    def verify_chain(self) -> bool:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM serving_receipts WHERE serving_party_id=? ORDER BY sequence",
                (self.serving_party_id,),
            ).fetchall()
            previous = self._GENESIS
            seen = set()
            for expected, row in enumerate(rows, start=1):
                receipt = ServingAdmissionReceipt(
                    sequence=row["sequence"], serving_party_id=row["serving_party_id"],
                    request_id=row["request_id"], caller_agent_id=row["caller_agent_id"],
                    caller_receipt_digest=row["caller_receipt_digest"],
                    call_digest=row["call_digest"], decision=row["decision"],
                    reason_code=row["reason_code"], occurred_at_epoch=row["occurred_at_epoch"],
                    previous_receipt_digest=row["previous_receipt_digest"],
                )
                key = (receipt.caller_agent_id, receipt.caller_receipt_digest)
                if receipt.sequence != expected or receipt.previous_receipt_digest != previous:
                    return False
                if key in seen:
                    return False
                digest = _digest(_canonical(asdict(receipt)))
                if digest != row["receipt_digest"]:
                    return False
                seen.add(key)
                previous = digest
            return True

    def close(self) -> None:
        with self._lock:
            self._db.close()
