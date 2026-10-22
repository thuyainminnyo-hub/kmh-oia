"""Minimal EduAutomate payment-record MVP API.

This service records internal payment claims and an explicit admin decision.
It does NOT connect to a bank, inspect bank statements, or independently prove
that funds settled. Admin-approved records are internal attestations only.

The shared-token mode is a trusted, isolated local prototype mode only. If
EDUAUTOMATE_AUTH_MODE=identity is selected, each request must carry a
server-verifiable identity assertion in the signed HS256 token implemented
below. Do not expose this prototype publicly; production should use an
established identity provider, tenant RBAC, TLS, managed secrets, and a
reviewed deployment model.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.tenant_identity import is_canonical_tenant_id


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


# Prototype shared secret authentication. Not production user or tenant identity.
def _configured_secret(name: str, failure: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise HTTPException(status_code=503, detail=failure)
    return value


def require_api_token(
    x_api_token: str | None = Header(default=None, alias="X-API-Token"),
) -> None:
    expected = os.environ.get("EDUAUTOMATE_API_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="API authentication is not configured")
    if x_api_token is None or not hmac.compare_digest(x_api_token, expected):
        raise HTTPException(status_code=401, detail="API authentication failed")


def require_configured_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> str:
    """Shared-token admin gate for isolated prototype mode only."""
    expected = os.environ.get("EDUAUTOMATE_ADMIN_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Admin approval is not configured")
    if x_admin_token is None or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Admin authentication failed")
    actor = os.environ.get("EDUAUTOMATE_ADMIN_ACTOR_ID", "").strip()
    if not actor or len(actor) > 128:
        raise HTTPException(status_code=503, detail="Admin actor identity is not configured")
    return actor


def _b64url_decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid identity assertion") from exc


def _verify_identity_token(authorization: str | None) -> dict[str, object]:
    """Verify a narrowly defined HS256 JWT-like assertion for isolated prototype tests.

    Production should replace this local verifier with a reviewed OIDC/JWKS
    integration. Required claims: sub, tenant_id, role, exp. Optional student_id.
    """
    secret = os.environ.get("EDUAUTOMATE_IDENTITY_HS256_SECRET", "")
    issuer = os.environ.get("EDUAUTOMATE_IDENTITY_ISSUER", "").strip()
    audience = os.environ.get("EDUAUTOMATE_IDENTITY_AUDIENCE", "").strip()
    if not secret or not issuer or not audience:
        raise HTTPException(status_code=503, detail="Identity authentication is not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer identity assertion required")
    token = authorization[7:].strip()
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Invalid identity assertion")
    head_part, claims_part, sig_part = parts
    try:
        header = json.loads(_b64url_decode(head_part))
        claims = json.loads(_b64url_decode(claims_part))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid identity assertion") from exc
    if not isinstance(header, dict) or header.get("alg") != "HS256" or header.get("typ", "JWT") != "JWT":
        raise HTTPException(status_code=401, detail="Unsupported identity assertion")
    signing_input = f"{head_part}.{claims_part}".encode("ascii")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_decode(sig_part), expected_sig):
        raise HTTPException(status_code=401, detail="Invalid identity signature")
    now = int(time.time())
    if not isinstance(claims, dict):
        raise HTTPException(status_code=401, detail="Invalid identity claims")
    if claims.get("iss") != issuer or claims.get("aud") != audience:
        raise HTTPException(status_code=401, detail="Invalid identity issuer or audience")
    if not isinstance(claims.get("exp"), int) or isinstance(claims.get("exp"), bool) or claims["exp"] <= now:
        raise HTTPException(status_code=401, detail="Expired or invalid identity assertion")
    # Honor optional JWT time claims when supplied; malformed or not-yet-valid
    # assertions must not be accepted by this prototype verifier.
    if "nbf" in claims and (
        not isinstance(claims["nbf"], int)
        or isinstance(claims["nbf"], bool)
        or claims["nbf"] > now
    ):
        raise HTTPException(status_code=401, detail="Identity assertion is not yet valid")
    if "iat" in claims and (
        not isinstance(claims["iat"], int)
        or isinstance(claims["iat"], bool)
        or claims["iat"] > now
    ):
        raise HTTPException(status_code=401, detail="Identity assertion issued in the future")
    if not isinstance(claims.get("sub"), str) or not claims["sub"].strip():
        raise HTTPException(status_code=401, detail="Identity subject missing")
    if not isinstance(claims.get("tenant_id"), str) or not claims["tenant_id"].strip():
        raise HTTPException(status_code=401, detail="Identity tenant missing")
    if not is_canonical_tenant_id(claims["tenant_id"]):
        raise HTTPException(status_code=401, detail="Identity tenant identifier is not canonical")
    if not isinstance(claims.get("role"), str) or not claims["role"].strip():
        raise HTTPException(status_code=401, detail="Identity role missing")
    return claims


def require_api_identity(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, object]:
    return _verify_identity_token(authorization)


def require_admin_identity(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, object]:
    claims = _verify_identity_token(authorization)
    if claims.get("role") not in ("admin", "payment_admin"):
        raise HTTPException(status_code=403, detail="Admin role required")
    return claims


def _identity_mode() -> str:
    mode = os.environ.get("EDUAUTOMATE_AUTH_MODE", "shared_token").strip().lower()
    if mode not in ("shared_token", "identity"):
        raise HTTPException(status_code=503, detail="Unsupported authentication mode")
    return mode


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # In identity mode this must match the authenticated subject's student scope;
    # only a role explicitly allowed to create for a tenant may create for others.
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
            if parsed.scheme or parsed.netloc or value.startswith("//") or value.lower().startswith("www."):
                raise ValueError("evidence_reference must be an opaque reference ID, not a URL")
        return value


production_mode = os.environ.get("EDUAUTOMATE_ENV", "").strip().lower() == "production"

app = FastAPI(
    docs_url=None if production_mode else "/docs",
    redoc_url=None if production_mode else "/redoc",
    openapi_url=None if production_mode else "/openapi.json",
    title="EduAutomate Payment Record MVP",
    version="0.1.1",
    description=(
        "Internal payment-record workflow. Admin decisions are internal attestations; "
        "this service does not independently verify bank settlement. Identity mode "
        "is an isolated prototype control and is not a production identity-provider integration."
    ),
)


@app.on_event("startup")
def startup() -> None:
    init_db()


def _to_payment(row: sqlite3.Row) -> PaymentOut:
    return PaymentOut(**dict(row))


def _get_record_by_id(payment_id: str) -> sqlite3.Row:
    with connect_db() as conn:
        row = conn.execute("SELECT * FROM payments WHERE payment_id=?", (payment_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return row


def _authorize_record_read(row: sqlite3.Row, claims: dict[str, object] | None) -> None:
    # Shared-token reads are an isolated local prototype path only.
    if _identity_mode() == "shared_token":
        return
    if claims is None:
        raise HTTPException(status_code=401, detail="Authenticated identity required")
    # Tenant scope is not persisted in the payment schema yet. Do not guess or
    # infer tenant ownership from currency/student_id. Only deny all identity-mode
    # reads until a reviewed tenant schema migration and authorization tests exist.
    raise HTTPException(
        status_code=503,
        detail="Identity-mode reads are disabled until tenant-scoped persistence and authorization are implemented",
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    # Liveness only: do not create/open the database as a health-check side effect.
    # This endpoint does not claim database readiness or payment-provider health.
    return {"status": "ok", "service": "eduautomate-payment-record-mvp"}


@app.post("/v1/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=200),
    _api_auth: None = Depends(require_api_token),
) -> PaymentOut:
    # The single shared API token does not identify a student or tenant.
    # Fail closed by default; explicitly opt in only for isolated local prototype use.
    if os.environ.get("EDUAUTOMATE_SHARED_TOKEN_PROTOTYPE_ENABLED", "").strip().lower() != "true":
        raise HTTPException(
            status_code=503,
            detail="Shared-token writes are disabled until a scoped identity adapter is configured",
        )
    if _identity_mode() == "identity":
        # Fail closed while persistence does not include tenant_id and trusted identity
        # claims have not been integrated end-to-end. This prevents an unsafe partial rollout.
        raise HTTPException(status_code=503, detail="Identity mode is not enabled for writes until tenant schema migration is implemented")
    init_db()
    now = utc_now()
    payment_id = "pay_" + uuid.uuid4().hex
    fingerprint = _canonical_hash(payload.model_dump())
    with connect_db() as conn:
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
            return _to_payment(values)
        conn.execute(
            """
            INSERT INTO payments (
                payment_id, student_id, amount_minor, currency, purpose, status,
                payment_method, execution_id, idempotency_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', 'manual_bank_transfer', ?, ?, ?, ?)
            """,
            (payment_id, payload.student_id, payload.amount_minor, payload.currency,
             payload.purpose, payload.execution_id, idempotency_key, now, now),
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
    x_api_token: str | None = Header(default=None, alias="X-API-Token"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> PaymentOut:
    mode = _identity_mode()
    if mode == "identity":
        # Validate the assertion, then deny before touching payment storage.
        # Tenant scope is not persisted and identity-mode reads are not enabled.
        _verify_identity_token(authorization)
        raise HTTPException(
            status_code=503,
            detail="Identity-mode reads are disabled until tenant-scoped persistence and authorization are implemented",
        )
    # Shared-token reads are local synthetic-prototype behavior only.
    # The shared token does not establish student ownership or tenant scope.
    if os.environ.get("EDUAUTOMATE_SHARED_TOKEN_PROTOTYPE_ENABLED", "").strip().lower() != "true":
        raise HTTPException(
            status_code=503,
            detail="Shared-token reads are disabled unless local prototype mode is explicitly enabled",
        )
    expected = os.environ.get("EDUAUTOMATE_API_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="API authentication is not configured")
    if x_api_token is None or not hmac.compare_digest(x_api_token, expected):
        raise HTTPException(status_code=401, detail="API authentication failed")
    row = _get_record_by_id(payment_id)
    return _to_payment(row)


@app.post("/v1/payments/{payment_id}/admin-decision", response_model=PaymentOut)
def admin_decision(
    payment_id: str,
    payload: AdminDecision,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> PaymentOut:
    if _identity_mode() == "identity":
        raise HTTPException(status_code=503, detail="Identity-mode admin decisions require the reviewed identity adapter and schema migration")
    if os.environ.get("EDUAUTOMATE_SHARED_TOKEN_PROTOTYPE_ENABLED", "").strip().lower() != "true":
        raise HTTPException(
            status_code=503,
            detail="Shared-token admin decisions are disabled unless local prototype mode is explicitly enabled",
        )
    actor_id = require_configured_admin(x_admin_token)
    init_db()
    now = utc_now()
    target = "confirmed" if payload.decision == "confirm" else "rejected"
    if target == "confirmed" and not payload.evidence_reference:
        raise HTTPException(status_code=422, detail="Admin confirmation requires an opaque evidence reference ID")
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
            (target, now, now if target == "confirmed" else None, actor_id if target == "confirmed" else None,
             payload.note, payload.evidence_reference, payment_id),
        )
        event_payload = {
            "payment_id": payment_id, "decision": payload.decision, "actor_id": actor_id,
            "occurred_at": now, "note": payload.note,
            "evidence_reference": payload.evidence_reference,
            "evidence_class": "internal_admin_attestation",
        }
        conn.execute(
            """
            INSERT INTO payment_events
              (event_id, payment_id, event_type, actor_id, occurred_at, reason, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("evt_" + uuid.uuid4().hex, payment_id, "admin_" + payload.decision,
             actor_id, now, payload.note + ("; evidence_reference=" + payload.evidence_reference if payload.evidence_reference else ""),
             _canonical_hash(event_payload)),
        )
        updated = conn.execute("SELECT * FROM payments WHERE payment_id=?", (payment_id,)).fetchone()
        return _to_payment(updated)
