"""Pilot trust primitives for authenticated QA and independently retained audit checkpoints.

This module uses HMAC-SHA256 with externally provisioned keys. It is not a
public-key signature system: verifiers need access to the shared secret.
The SQLite trust store must live outside the JSONL audit directory and be
backed up/controlled as a separate trust boundary.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _require_key(key: bytes) -> None:
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("HMAC key must contain at least 32 bytes")


def _verify_audit_events(events: list[dict]) -> bool:
    """Verify every JSONL event hash and previous-hash link before checkpointing."""
    if not isinstance(events, list) or not events:
        return False
    expected_previous = "0" * 64
    for event in events:
        if not isinstance(event, dict):
            return False
        recorded = event.get("event_hash")
        if (not isinstance(recorded, str) or len(recorded) != 64
                or any(char not in "0123456789abcdef" for char in recorded)):
            return False
        if event.get("previous_hash") != expected_previous:
            return False
        unhashed = {key: value for key, value in event.items() if key != "event_hash"}
        try:
            canonical = json.dumps(unhashed, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError):
            return False
        calculated = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(recorded, calculated):
            return False
        expected_previous = recorded
    return True


@dataclass(frozen=True)
class ReviewerPrincipal:
    subject: str
    roles: tuple[str, ...]
    issuer: str
    audience: str
    issued_at: int
    expires_at: int
    nonce: str


class ReviewerTokenAuthority:
    """Issue and verify short-lived, HMAC-authenticated reviewer assertions."""

    def __init__(self, *, key_id: str, key: bytes, issuer: str, audience: str) -> None:
        _require_key(key)
        if not all(isinstance(v, str) and v.strip() for v in (key_id, issuer, audience)):
            raise ValueError("key_id, issuer and audience are required")
        self.key_id, self._key, self.issuer, self.audience = key_id, key, issuer, audience

    def issue(self, *, subject: str, roles: Iterable[str], ttl_seconds: int = 300,
              now: int | None = None, nonce: str | None = None) -> str:
        current = int(time.time()) if now is None else now
        role_list = sorted(set(roles))
        if not isinstance(subject, str) or not subject.strip() or not role_list:
            raise ValueError("subject and at least one role are required")
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or not 1 <= ttl_seconds <= 900:
            raise ValueError("ttl_seconds must be between 1 and 900")
        if any(not isinstance(role, str) or not role.strip() for role in role_list):
            raise ValueError("roles must be non-empty strings")
        payload = {"kid": self.key_id, "iss": self.issuer, "aud": self.audience,
                   "sub": subject, "roles": role_list, "iat": current,
                   "exp": current + ttl_seconds, "nonce": nonce or secrets.token_urlsafe(24)}
        encoded = _canonical(payload)
        signature = hmac.new(self._key, encoded, hashlib.sha256).hexdigest()
        return encoded.hex() + "." + signature

    def verify(self, token: str, *, required_role: str, replay_store: "ReviewerReplayStore",
               now: int | None = None) -> ReviewerPrincipal:
        try:
            encoded_hex, supplied_signature = token.split(".", 1)
            encoded = bytes.fromhex(encoded_hex)
            payload = json.loads(encoded)
        except (AttributeError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid reviewer assertion") from exc
        expected = hmac.new(self._key, encoded, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied_signature):
            raise ValueError("invalid reviewer assertion signature")
        if _canonical(payload) != encoded or payload.get("kid") != self.key_id:
            raise ValueError("reviewer assertion key or encoding mismatch")
        current = int(time.time()) if now is None else now
        if payload.get("iss") != self.issuer or payload.get("aud") != self.audience:
            raise ValueError("reviewer assertion issuer or audience mismatch")
        if not isinstance(payload.get("iat"), int) or not isinstance(payload.get("exp"), int):
            raise ValueError("reviewer assertion timestamps are invalid")
        if payload["iat"] > current or payload["exp"] <= current or payload["exp"] - payload["iat"] > 900:
            raise ValueError("reviewer assertion is expired or outside its validity window")
        roles = payload.get("roles")
        if not isinstance(roles, list) or required_role not in roles:
            raise ValueError("reviewer is not authorized for the required role")
        subject, nonce = payload.get("sub"), payload.get("nonce")
        if not isinstance(subject, str) or not subject.strip() or not isinstance(nonce, str) or not nonce:
            raise ValueError("reviewer assertion identity is invalid")
        replay_store.claim(self.issuer, subject, nonce, payload["exp"])
        return ReviewerPrincipal(subject, tuple(roles), self.issuer, self.audience,
                                 payload["iat"], payload["exp"], nonce)


class ReviewerReplayStore:
    """Durable, single-host nonce store. Use a shared transactional DB multi-host."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS reviewer_nonces (
                issuer TEXT NOT NULL, subject TEXT NOT NULL, nonce TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                PRIMARY KEY (issuer, subject, nonce))""")

    def claim(self, issuer: str, subject: str, nonce: str, expires_at: int) -> None:
        try:
            with sqlite3.connect(self.path, timeout=10, isolation_level="IMMEDIATE") as db:
                db.execute("INSERT INTO reviewer_nonces VALUES (?, ?, ?, ?)",
                           (issuer, subject, nonce, expires_at))
        except sqlite3.IntegrityError as exc:
            raise ValueError("reviewer assertion replay detected") from exc

    def health_check(self) -> bool:
        try:
            with sqlite3.connect(self.path) as db:
                db.execute("SELECT issuer, subject, nonce, expires_at FROM reviewer_nonces LIMIT 1").fetchall()
            return True
        except sqlite3.Error:
            return False


@dataclass(frozen=True)
class AuditCheckpoint:
    sequence: int
    event_count: int
    head_hash: str
    created_at: int
    key_id: str
    signature: str

    def unsigned(self) -> dict:
        return {"sequence": self.sequence, "event_count": self.event_count, "head_hash": self.head_hash,
                "created_at": self.created_at, "key_id": self.key_id}


class IndependentCheckpointStore:
    """SQLite checkpoint ledger; provision its file outside the local audit directory."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS audit_checkpoints (
                sequence INTEGER PRIMARY KEY, event_count INTEGER NOT NULL, head_hash TEXT NOT NULL,
                created_at INTEGER NOT NULL, key_id TEXT NOT NULL,
                signature TEXT NOT NULL)""")

    def append(self, checkpoint: AuditCheckpoint) -> None:
        with sqlite3.connect(self.path, timeout=10, isolation_level="IMMEDIATE") as db:
            latest = db.execute("SELECT sequence, event_count FROM audit_checkpoints ORDER BY sequence DESC LIMIT 1").fetchone()
            expected = 1 if latest is None else latest[0] + 1
            prior_event_count = 0 if latest is None else latest[1]
            if checkpoint.sequence != expected or checkpoint.event_count <= prior_event_count:
                raise ValueError("checkpoint sequence or event count is not advancing")
            db.execute("INSERT INTO audit_checkpoints VALUES (?, ?, ?, ?, ?, ?)",
                       (checkpoint.sequence, checkpoint.event_count, checkpoint.head_hash,
                        checkpoint.created_at, checkpoint.key_id, checkpoint.signature))

    def latest(self) -> AuditCheckpoint | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("""SELECT sequence, event_count, head_hash, created_at, key_id, signature
                                FROM audit_checkpoints ORDER BY sequence DESC LIMIT 1""").fetchone()
        return AuditCheckpoint(*row) if row else None

    def health_check(self) -> bool:
        try:
            with sqlite3.connect(self.path) as db:
                db.execute("SELECT sequence FROM audit_checkpoints LIMIT 1").fetchall()
            return True
        except sqlite3.Error:
            return False


class AuditCheckpointAuthority:
    """HMAC-sign audit heads and compare them with separately retained checkpoints."""

    def __init__(self, *, key_id: str, key: bytes) -> None:
        _require_key(key)
        if not isinstance(key_id, str) or not key_id.strip():
            raise ValueError("key_id is required")
        self.key_id, self._key = key_id, key

    def create(self, events: list[dict], store: IndependentCheckpointStore,
               *, now: int | None = None) -> AuditCheckpoint:
        if not events:
            raise ValueError("cannot checkpoint an empty audit chain")
        if not _verify_audit_events(events):
            raise ValueError("cannot checkpoint an invalid or unverified audit chain")
        previous = store.latest()
        sequence = 1 if previous is None else previous.sequence + 1
        if previous is not None and len(events) <= previous.event_count:
            raise ValueError("audit event count must advance beyond the prior checkpoint")
        head = events[-1].get("event_hash")
        if not isinstance(head, str) or len(head) != 64:
            raise ValueError("audit chain head is invalid")
        unsigned = {"sequence": sequence, "event_count": len(events), "head_hash": head,
                    "created_at": int(time.time()) if now is None else now,
                    "key_id": self.key_id}
        signature = hmac.new(self._key, _canonical(unsigned), hashlib.sha256).hexdigest()
        checkpoint = AuditCheckpoint(**unsigned, signature=signature)
        store.append(checkpoint)
        return checkpoint

    def verify(self, events: list[dict], store: IndependentCheckpointStore) -> bool:
        checkpoint = store.latest()
        if checkpoint is None or not _verify_audit_events(events):
            return False
        if len(events) != checkpoint.event_count:
            return False
        if events[-1].get("event_hash") != checkpoint.head_hash or checkpoint.key_id != self.key_id:
            return False
        expected = hmac.new(self._key, _canonical(checkpoint.unsigned()), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, checkpoint.signature)


def record_authenticated_qa_decision(*, audit_sink, authority: ReviewerTokenAuthority,
                                     replay_store: ReviewerReplayStore, reviewer_token: str,
                                     job_id: str, output_sha256: str, decision: str,
                                     required_role: str = "qa_approver", now: int | None = None) -> dict:
    """Delegate QA admission to the audit sink's authenticated reviewer boundary."""
    return audit_sink.record_qa_decision(
        job_id=job_id, output_sha256=output_sha256, decision=decision,
        reviewer_token=reviewer_token, reviewer_authority=authority,
        reviewer_replay_store=replay_store, required_role=required_role, now=now,
    )
