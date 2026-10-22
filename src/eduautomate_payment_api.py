"""Minimal EduAutomate payment-record MVP API.

This service records internal payment claims and an explicit admin decision.
It does NOT connect to a bank, inspect bank statements, or independently prove
that funds settled. Admin-approved records are internal attestations only.

Run locally (after installing FastAPI and Uvicorn in a project virtualenv):
    EDUAUTOMATE_DB_PATH=runtime/eduautomate-payments.sqlite3 \
      uvicorn src.eduautomate_payment_api:app --host 127.0.0.1 --port 8000

Keep this dev-only API bound to localhost until authentication, authorization,
TLS, and a production deployment model are configured.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def get_db_path() -> str:
    path = os.environ.get("EDUAUTOMATE_DB_PATH", "runtime/eduautomate-payments.sqlite3").strip()
    if not path or path == ":memory:":
        raise RuntimeError("EDUAUTOMATE_DB_PATH must be a persistent file path")
    return path


@contextmanager
def connect_db() -> Iterator[sqlite3.Connection]:
    path = Path(get_db_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=10000")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connect_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
                currency TEXT NOT NULL CHECK (length(currency) = 3),
                purpose TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN (
                    'pending', 'confirmed', 'rejected'
                )),
                payment_method TEXT NOT NULL CHECK (payment_method = 'manual_bank_transfer'),
                execution_id TEXT,
                idempotency_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                confirmed_at TEXT,
                confirmed_by TEXT,
                admin_note TEXT,
                evidence_reference TEXT
            )
            """
        )
        # Lightweight migration for a database created by an earlier prototype version.
        payment_columns = {row[1] for row in conn.execute("PRAGMA table_info(payments)").fetchall()}
        if "evidence_reference" not in payment_columns:
            conn.execute("ALTER TABLE payments ADD COLUMN evidence_reference TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payment_events (
                event_id TEXT PRIMARY KEY,
                payment_id TEXT NOT NULL REFERENCES payments(payment_id),
                event_type TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                reason TEXT NOT NULL,
                content_hash TEXT NOT NULL
            )
            """
        )


def require_api_token(
    x_api_token: str | None = Header(default=None, alias="X-API-Token"),
) -> str:
    """Resolve a prototype caller to one server-configured student scope.

    EDUAUTOMATE_API_TOKENS_JSON must be a JSON object mapping distinct opaque
    API tokens to student IDs, for example {"token-value":"stu_123"}.
    This is a localhost/prototype control, not a replacement for production
    identity, tenant RBAC, token rotation, or a managed identity provider.
    """
    raw_mapping = os.environ.get("EDUAUTOMATE_API_TOKENS_JSON", "").strip()
    if not raw_mapping:
        raise HTTPException(status_code=503, detail="Scoped API authentication is not configured")
    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        parsed: dict[str, object] = {}
        for key, value in pairs:
            if key in parsed:
                raise ValueError("Duplicate key in scoped API authentication configuration")
            parsed[key] = value
        return parsed

    try:
        token_to_student = json.loads(raw_mapping, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=503, detail="Scoped API authentication configuration is invalid")
    if (
        not isinstance(token_to_student, dict)
        or not token_to_student
        or any(
            not isinstance(token, str)
            or not token
            or not isinstance(student_id, str)
            or not student_id.strip()
            or len(student_id) > 128
            for token, student_id in token_to_student.items()
        )
    ):
        raise HTTPException(status_code=503, detail="Scoped API authentication configuration is invalid")
    if x_api_token is None:
        raise HTTPException(status_code=401, detail="API authentication failed")
    matched_student_id = None
    for expected_token, student_id in token_to_student.items():
        if __import__("hmac").compare_digest(x_api_token, expected_token):
            matched_student_id = student_id
    if matched_student_id is None:
        raise HTTPException(status_code=401, detail="API authentication failed")
    return matched_student_id


def require_configured_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> str:
    """MVP gate: shared admin token plus server-configured actor label; not production RBAC."""
    expected = os.environ.get("EDUAUTOMATE_ADMIN_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Admin approval is not configured")
    if x_admin_token is None or not __import__("hmac").compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Admin authentication failed")
    actor = os.environ.get("EDUAUTOMATE_ADMIN_ACTOR_ID", "").strip()
    if not actor or len(actor) > 128:
        raise HTTPException(status_code=503, detail="Admin actor identity is not configured")
    return actor


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    student_id: str = Field(min_length=1, max_length=128)
    amount_minor: int = Field(strict=True, gt=0, le=10**12)
    currency: Literal["MMK"] = "MMK"
    purpose: str = Field(min_length=1, max_length=120)
    execution_id: str | None = Field(default=None, max_length=128)


class PaymentOut(BaseModel):
    payment_id: str
    student_id: str
    amount_minor: int
    currency: str
    purpose: str
    status: str
    payment_method: str
    execution_id: str | None
    created_at: str
    updated_at: str
    confirmed_at: str | None
    confirmed_by: str | None
    admin_note: str | None
    evidence_reference: str | None


class AdminDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    decision: Literal["confirm", "reject"]
    note: str = Field(min_length=3, max_length=500)
    evidence_reference: str | None = Field(default=None, min_length=3, max_length=300)

    @field_validator("evidence_reference")
    @classmethod
    def evidence_reference_must_be_opaque(cls, value: str | None) -> str | None:
        if value:
            parsed = urlsplit(value)
            if (
                parsed.scheme
                or parsed.netloc
                or value.startswith("//")
                or value.lower().startswith("www.")
            ):
                raise ValueError("evidence_reference must be an opaque reference ID, not a URL")
        return value


app = FastAPI(
    title="EduAutomate Payment Record MVP",
    version="0.1.0",
    description=(
        "Internal payment-record workflow. Admin decisions are internal attestations; "
        "this service does not independently verify bank settlement."
    ),
)


@app.on_event("startup")
def startup() -> None:
    init_db()


def _to_payment(row: sqlite3.Row) -> PaymentOut:
    return PaymentOut(**dict(row))


@app.get("/healthz")
def healthz() -> dict[str, str]:
    init_db()
    return {"status": "ok", "service": "eduautomate-payment-record-mvp"}


@app.post("/v1/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=200),
    authenticated_student_id: str = Depends(require_api_token),
) -> PaymentOut:
    if payload.student_id != authenticated_student_id:
        raise HTTPException(status_code=403, detail="Caller is not authorized for this student")
    init_db()
    now = utc_now()
    payment_id = "pay_" + uuid.uuid4().hex
    fingerprint = _canonical_hash(payload.model_dump())
    with connect_db() as conn:
        # Serialize the idempotency lookup + insert so concurrent retries share one result.
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            "SELECT p.*, e.content_hash AS create_fingerprint FROM payments p "
            "LEFT JOIN payment_events e ON e.payment_id=p.payment_id AND e.event_type='created' "
            "WHERE p.idempotency_key=?",
            (idempotency_key,),
        ).fetchone()
        if existing:
            if existing["create_fingerprint"] != fingerprint:
                raise HTTPException(status_code=409, detail="Idempotency key reused with different payload")
            values = dict(existing)
            values.pop("create_fingerprint", None)
            return _to_payment(values)  # Same request returns original resource.
        conn.execute(
            """
            INSERT INTO payments (
                payment_id, student_id, amount_minor, currency, purpose, status,
                payment_method, execution_id, idempotency_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', 'manual_bank_transfer', ?, ?, ?, ?)
            """,
            (
                payment_id, payload.student_id, payload.amount_minor, payload.currency,
                payload.purpose, payload.execution_id, idempotency_key, now, now,
            ),
        )
        conn.execute(
            """
            INSERT INTO payment_events
              (event_id, payment_id, event_type, actor_id, occurred_at, reason, content_hash)
            VALUES (?, ?, 'created', 'system', ?, 'payment record created as pending', ?)
            """,
            ("evt_" + uuid.uuid4().hex, payment_id, now, fingerprint),
        )
        row = conn.execute("SELECT * FROM payments WHERE payment_id=?", (payment_id,)).fetchone()
        return _to_payment(row)


@app.get("/v1/payments/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: str,
    authenticated_student_id: str = Depends(require_api_token),
) -> PaymentOut:
    init_db()
    with connect_db() as conn:
        row = conn.execute("SELECT * FROM payments WHERE payment_id=?", (payment_id,)).fetchone()
    # Use the same non-disclosing response for missing and out-of-scope records.
    if row is None or row["student_id"] != authenticated_student_id:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return _to_payment(row)


@app.post("/v1/payments/{payment_id}/admin-decision", response_model=PaymentOut)
def admin_decision(
    payment_id: str,
    payload: AdminDecision,
    actor_id: str = Depends(require_configured_admin),
) -> PaymentOut:
    init_db()
    now = utc_now()
    target = "confirmed" if payload.decision == "confirm" else "rejected"
    if target == "confirmed" and not payload.evidence_reference:
        raise HTTPException(status_code=422, detail="Admin confirmation requires an opaque evidence reference ID")
    # This changes internal workflow status only; it is not bank/provider verification.
    with connect_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM payments WHERE payment_id=?", (payment_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Payment record not found")
        if row["status"] != "pending":
            raise HTTPException(status_code=409, detail="Only pending payment records can receive an admin decision")
        conn.execute(
            """
            UPDATE payments SET status=?, updated_at=?, confirmed_at=?, confirmed_by=?, admin_note=?, evidence_reference=?
            WHERE payment_id=? AND status='pending'
            """,
            (target, now, now if target == "confirmed" else None, actor_id if target == "confirmed" else None, payload.note, payload.evidence_reference, payment_id),
        )
        event_payload = {
            "payment_id": payment_id,
            "decision": payload.decision,
            "actor_id": actor_id,
            "occurred_at": now,
            "note": payload.note,
            "evidence_reference": payload.evidence_reference,
            "evidence_class": "internal_admin_attestation",
        }
        conn.execute(
            """
            INSERT INTO payment_events
              (event_id, payment_id, event_type, actor_id, occurred_at, reason, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "evt_" + uuid.uuid4().hex, payment_id, "admin_" + payload.decision,
                actor_id, now, payload.note + ("; evidence_reference=" + payload.evidence_reference if payload.evidence_reference else ""), _canonical_hash(event_payload),
            ),
        )
        updated = conn.execute("SELECT * FROM payments WHERE payment_id=?", (payment_id,)).fetchone()
        return _to_payment(updated)
