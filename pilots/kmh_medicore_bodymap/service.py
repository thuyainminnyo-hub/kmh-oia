"""Local-only synthetic Orthopedics body-map pilot with transactional audit controls.

This module is a prototype, not a clinical system. It performs no network calls and
must never be used with real patient records.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


class BodyMapError(ValueError):
    """A body-map input or operation failed a defined control."""


_ALLOWED_ANATOMY = {
    "SKULL": "Skull",
    "SPINE": "Spine",
    "PELVIS": "Pelvis",
    "UPPER_LIMB": "Upper limb",
    "LOWER_LIMB": "Lower limb",
}
_ALLOWED_FINDINGS = {"fracture", "dislocation", "arthritis", "bone_lesion", "other"}
_ALLOWED_TREATMENTS = {"closed_reduction", "cast_or_splint", "internal_fixation", "observation", "other"}
_ALLOWED_STATUSES = {"draft", "reviewed", "signed", "amended"}
_SAFE_REF = re.compile(r"^SYN-(?:BMA|ENC|ACTOR)-[A-Za-z0-9-]{1,40}$")


def utc_now() -> str:
    """Return an aware UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def validate_annotation(annotation: dict[str, Any]) -> dict[str, Any]:
    """Validate the pilot's strict schema subset and return a JSON-safe copy."""
    if not isinstance(annotation, dict):
        raise BodyMapError("annotation must be an object")
    required = {
        "schema_version", "annotation_id", "encounter_ref", "data_classification",
        "specialty", "anatomy_system", "anatomy_code", "region", "view", "laterality",
        "finding", "treatment", "status", "author_ref", "created_at", "updated_at",
    }
    allowed = required | {"signed_at", "amends_annotation_ref"}
    if set(annotation) - allowed:
        raise BodyMapError("annotation contains unknown fields")
    if required - set(annotation):
        raise BodyMapError("annotation is missing required fields")
    if annotation["schema_version"] != "0.1" or annotation["data_classification"] != "synthetic":
        raise BodyMapError("only schema 0.1 synthetic records are allowed")
    if annotation["specialty"] != "orthopedics" or annotation["anatomy_system"] != "KMH-ANATOMY-LOCAL-0.1":
        raise BodyMapError("unsupported specialty or anatomy system")
    for key, prefix in (("annotation_id", "SYN-BMA-"), ("encounter_ref", "SYN-ENC-"), ("author_ref", "SYN-ACTOR-")):
        value = annotation[key]
        if not isinstance(value, str) or not value.startswith(prefix) or not _SAFE_REF.fullmatch(value):
            raise BodyMapError(f"{key} must be a valid synthetic reference")
    anatomy = annotation["anatomy_code"]
    if anatomy not in _ALLOWED_ANATOMY or annotation["region"] != _ALLOWED_ANATOMY[anatomy]:
        raise BodyMapError("anatomy code and region do not match the local registry")
    if annotation["view"] not in {"front", "back", "both"}:
        raise BodyMapError("view must be front, back, or both")
    if annotation["laterality"] not in {"left", "right", "bilateral", "midline", "not_applicable"}:
        raise BodyMapError("invalid laterality")
    if anatomy == "SKULL" and annotation["laterality"] != "midline":
        raise BodyMapError("SKULL requires midline laterality in this pilot registry")
    if annotation["finding"] not in _ALLOWED_FINDINGS:
        raise BodyMapError("unsupported finding")
    treatment = annotation["treatment"]
    if not isinstance(treatment, dict) or set(treatment) != {"code", "status"}:
        raise BodyMapError("treatment must contain only code and status")
    if treatment["code"] not in _ALLOWED_TREATMENTS or treatment["status"] not in {"proposed", "planned", "performed", "cancelled"}:
        raise BodyMapError("invalid treatment code or status")
    if annotation["status"] not in _ALLOWED_STATUSES:
        raise BodyMapError("invalid annotation status")
    if annotation["status"] == "signed":
        if not isinstance(annotation.get("signed_at"), str):
            raise BodyMapError("signed records require signed_at")
    for key in ("created_at", "updated_at"):
        value = annotation[key]
        if not isinstance(value, str):
            raise BodyMapError(f"{key} must be an ISO timestamp")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise BodyMapError(f"{key} must be an ISO timestamp") from exc
        if parsed.tzinfo is None:
            raise BodyMapError(f"{key} must include a timezone")
    if annotation["status"] == "signed":
        try:
            signed = datetime.fromisoformat(annotation["signed_at"].replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise BodyMapError("signed_at must be an ISO timestamp") from exc
        if signed.tzinfo is None:
            raise BodyMapError("signed_at must include a timezone")
    return json.loads(json.dumps(annotation))


class BodyMapStore:
    """SQLite local store with atomic annotation/audit writes and immutable audit rows."""

    def __init__(self, database_path: str | Path, authorized_actors: set[str]) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.authorized_actors = set(authorized_actors)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=2.0)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA foreign_keys = ON")
            db.execute("""CREATE TABLE IF NOT EXISTS annotations (
                annotation_id TEXT PRIMARY KEY,
                record_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS audit_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                occurred_at TEXT NOT NULL,
                actor_ref TEXT NOT NULL,
                action TEXT NOT NULL,
                outcome TEXT NOT NULL,
                correlation_ref TEXT NOT NULL
            )""")
            db.execute("""CREATE TRIGGER IF NOT EXISTS audit_no_update
                BEFORE UPDATE ON audit_events BEGIN
                SELECT RAISE(ABORT, 'audit events are append-only');
            END""")
            db.execute("""CREATE TRIGGER IF NOT EXISTS audit_no_delete
                BEFORE DELETE ON audit_events BEGIN
                SELECT RAISE(ABORT, 'audit events are append-only');
            END""")

    def create_annotation(self, annotation: dict[str, Any], actor_ref: str) -> dict[str, Any]:
        """Authorize and atomically persist one draft annotation plus minimal audit evidence."""
        safe = validate_annotation(annotation)
        if actor_ref not in self.authorized_actors:
            self._record_denial(actor_ref, "annotation.create", safe["annotation_id"])
            raise PermissionError("actor is not authorized for this local pilot")
        if actor_ref != safe["author_ref"]:
            self._record_denial(actor_ref, "annotation.create", safe["annotation_id"])
            raise PermissionError("actor_ref must match annotation author_ref")
        if safe["status"] != "draft":
            raise BodyMapError("pilot create operation accepts draft records only")
        if safe["treatment"]["status"] not in {"proposed", "planned"}:
            raise BodyMapError("new draft cannot claim treatment was performed or cancelled")
        now = utc_now()
        # One transaction ensures the record is not committed without its audit event.
        with self._connect() as db:
            db.execute("PRAGMA foreign_keys = ON")
            db.execute(
                "INSERT INTO annotations(annotation_id, record_json, created_at) VALUES (?, ?, ?)",
                (safe["annotation_id"], json.dumps(safe, sort_keys=True), now),
            )
            db.execute(
                """INSERT INTO audit_events(occurred_at, actor_ref, action, outcome, correlation_ref)
                   VALUES (?, ?, ?, ?, ?)""",
                (now, actor_ref, "annotation.create", "success", "corr-" + safe["annotation_id"]),
            )
        # Return the record only after both writes commit.
        return safe

    def _record_denial(self, actor_ref: str, action: str, correlation_ref: str) -> None:
        safe_actor = actor_ref if isinstance(actor_ref, str) and _SAFE_REF.fullmatch(actor_ref) else "SYN-ACTOR-unknown"
        safe_correlation = correlation_ref if isinstance(correlation_ref, str) and re.fullmatch(r"[A-Za-z0-9-]{1,80}", correlation_ref) else "invalid-ref"
        with self._connect() as db:
            db.execute(
                """INSERT INTO audit_events(occurred_at, actor_ref, action, outcome, correlation_ref)
                   VALUES (?, ?, ?, ?, ?)""",
                (utc_now(), safe_actor, action, "denied", safe_correlation),
            )

    def get_annotation(self, annotation_id: str, actor_ref: str) -> dict[str, Any]:
        """Read only for an explicitly authorized synthetic actor."""
        if actor_ref not in self.authorized_actors:
            self._record_denial(actor_ref, "annotation.read", annotation_id)
            raise PermissionError("actor is not authorized for this local pilot")
        with self._connect() as db:
            row = db.execute("SELECT record_json FROM annotations WHERE annotation_id = ?", (annotation_id,)).fetchone()
        if row is None:
            raise KeyError("annotation not found")
        return json.loads(row["record_json"])

    def list_audit_events(self) -> list[dict[str, Any]]:
        """Expose minimal audit metadata for tests and local verification."""
        with self._connect() as db:
            rows = db.execute(
                "SELECT occurred_at, actor_ref, action, outcome, correlation_ref FROM audit_events ORDER BY event_id"
            ).fetchall()
        return [dict(row) for row in rows]
