#!/usr/bin/env python3
"""Versioned local JSONL registry and fail-closed execution authorization guard.

This is a pilot persistence adapter, not tamper-proof storage. Production use requires
an access-controlled backend, transactional concurrency control, retention policy,
and independently verified append-only/WORM audit storage.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

GENESIS_HASH = "0" * 64


class RegistryError(ValueError):
    """Registry data or integrity check failed."""


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_hash(envelope):
    payload = {k: v for k, v in envelope.items() if k != "entry_hash"}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def read_entries(path):
    file_path = Path(path)
    if not file_path.exists():
        return []
    entries = []
    previous_hash = GENESIS_HASH
    latest_versions = {}
    for line_number, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise RegistryError(f"blank line at {line_number}")
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RegistryError(f"invalid JSON at line {line_number}: {exc}") from exc
        required = {"case_id", "version", "record", "previous_hash", "entry_hash", "stored_at"}
        if not isinstance(entry, dict) or not required.issubset(entry):
            raise RegistryError(f"invalid envelope at line {line_number}")
        if entry["previous_hash"] != previous_hash:
            raise RegistryError(f"broken hash chain at line {line_number}")
        if entry["entry_hash"] != record_hash(entry):
            raise RegistryError(f"entry hash mismatch at line {line_number}")
        case_id = entry["case_id"]
        expected_version = latest_versions.get(case_id, 0) + 1
        if entry["version"] != expected_version:
            raise RegistryError(f"non-sequential version for {case_id} at line {line_number}")
        latest_versions[case_id] = expected_version
        previous_hash = entry["entry_hash"]
        entries.append(entry)
    return entries


def save_version(path, record, *, stored_at=None):
    """Append a new version; refuses invalid records and never rewrites old entries."""
    from jsonschema import Draft202012Validator, FormatChecker

    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "cybersecurity-threat-record.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record))
    if errors:
        raise RegistryError("record failed schema validation: " + "; ".join(e.message for e in errors))
    case_id = record["case_id"]
    entries = read_entries(path)
    case_versions = [e["version"] for e in entries if e["case_id"] == case_id]
    previous_hash = entries[-1]["entry_hash"] if entries else GENESIS_HASH
    envelope = {
        "case_id": case_id,
        "version": max(case_versions, default=0) + 1,
        "record": record,
        "previous_hash": previous_hash,
        "stored_at": stored_at or datetime.now(timezone.utc).isoformat(),
    }
    envelope["entry_hash"] = record_hash(envelope)
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    # O_APPEND prevents accidental truncation, but this adapter does not claim
    # cross-process transactional locking or WORM-grade immutability.
    with file_path.open("a", encoding="utf-8") as stream:
        stream.write(canonical_json(envelope) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return envelope


def authorize_execution(record, action, *, now=None):
    """Return (allowed, reason); fail closed unless approval exactly matches scope."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        return False, "current time must include timezone"
    if not isinstance(record, dict):
        return False, "record must be an object"
    asset = record.get("asset") or {}
    threat = record.get("threat") or {}
    assessment = record.get("assessment") or {}
    approval = record.get("approval") or {}
    if threat.get("verification_status") != "verified":
        return False, "threat source is not verified"
    if assessment.get("applicability") != "affected":
        return False, "asset applicability is not confirmed affected"
    if assessment.get("decision") != action:
        return False, "requested action does not match assessment decision"
    if not asset.get("asset_id") or not asset.get("owner"):
        return False, "asset identity or responsible owner is missing"
    if approval.get("status") != "approved":
        return False, "approval status is not approved"
    if not approval.get("approver") or not approval.get("rollback_plan_ref"):
        return False, "approver or rollback plan is missing"
    scope = approval.get("scope")
    if not isinstance(scope, list) or f"asset:{asset['asset_id']}" not in scope or f"action:{action}" not in scope:
        return False, "approval scope does not match exact asset and action"
    try:
        approved_at = datetime.fromisoformat(approval["approved_at"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(approval["expires_at"].replace("Z", "+00:00"))
    except (KeyError, AttributeError, TypeError, ValueError):
        return False, "approval timestamps are missing or invalid"
    if approved_at.tzinfo is None or expires_at.tzinfo is None:
        return False, "approval timestamps must include timezone"
    if approved_at > now:
        return False, "approval is not effective yet"
    if expires_at <= now:
        return False, "approval has expired"
    if expires_at <= approved_at:
        return False, "approval expiry must be after approval time"
    return True, "approval is valid for the exact asset and action"


def verify_registry(path):
    """Validate the full local hash chain and return entry count."""
    return len(read_entries(path))
