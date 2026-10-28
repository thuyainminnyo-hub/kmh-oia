"""Read-only exact-ID patient history retrieval over synthetic JSON fixtures."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class RetrievalError(Exception):
    """Base class for controlled retrieval failures."""


class PatientNotFound(RetrievalError):
    """No patient has the requested exact identifier."""


class DuplicatePatientID(RetrievalError):
    """The fixture contains duplicate IDs; fail closed rather than guessing."""


class InvalidFixture(RetrievalError):
    """The fixture is malformed or violates the expected shape."""


def load_patients(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSON list of explicitly labelled synthetic records without modifying the file."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidFixture("fixture could not be read as valid JSON") from exc
    if not isinstance(payload, list):
        raise InvalidFixture("fixture root must be a JSON list")
    for record in payload:
        if not isinstance(record, dict) or not isinstance(record.get("patient_id"), str):
            raise InvalidFixture("each patient must be an object with a string patient_id")
        if not record["patient_id"].strip():
            raise InvalidFixture("patient_id must not be empty")
        if record.get("synthetic") is not True:
            raise InvalidFixture("each patient must be explicitly labelled synthetic=true")
        if not re.fullmatch(r"SYN-PAT-[A-Za-z0-9-]+", record["patient_id"]):
            raise InvalidFixture("patient_id must use the synthetic SYN-PAT- prefix")
        if not isinstance(record.get("visits"), list):
            raise InvalidFixture("each patient must contain a visits list")
    return payload


def retrieve_history(patients: list[dict[str, Any]], patient_id: str) -> dict[str, Any]:
    """Return the exact matching synthetic record; never fuzzy-match or infer data."""
    if not isinstance(patient_id, str) or not patient_id.strip():
        raise ValueError("patient_id must not be empty")
    matches = [record for record in patients if record.get("patient_id") == patient_id]
    if not matches:
        raise PatientNotFound("no exact patient ID match")
    if len(matches) != 1:
        raise DuplicatePatientID("duplicate exact patient IDs; retrieval blocked")
    # Return a JSON round-trip copy so callers cannot mutate the loaded source object.
    return json.loads(json.dumps(matches[0]))


def make_audit_event(request_id: str, outcome: str) -> dict[str, str]:
    """Create a PHI-minimizing audit event; deliberately excludes patient ID and history."""
    if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9._:-]{1,80}", request_id):
        raise ValueError("request_id must be 1-80 characters: letters, digits, dot, underscore, colon or hyphen only")
    if outcome not in {"SUCCESS", "NOT_FOUND", "BLOCKED", "ERROR"}:
        raise ValueError("unsupported audit outcome")
    from datetime import datetime, timezone

    return {
        "request_id": request_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "action": "patient_history_retrieval",
        "outcome": outcome,
    }
