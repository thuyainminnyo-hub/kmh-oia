"""Authorization-enforcing service boundary for the TGiTrailRun pilot.

The caller must authenticate the user and derive role from a trusted identity
provider before constructing/using this service. This module does not implement
authentication, network transport, or dispatch. Checkpoint scope is enforced only when
an upstream trusted adapter supplies the caller's allowed checkpoint IDs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from src.trailrun_incident_access import authorize, authorize_transition
from src.trailrun_incident_store import (
    IncidentStoreError,
    InvalidTransition,
    SQLiteIncidentStore,
)


class AccessDenied(PermissionError):
    """Raised when a trusted caller role lacks permission for an action."""


class InvalidIncidentPayload(ValueError):
    """Raised when a create payload does not match the published JSON Schema."""


_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "pilots" / "tgi-trailrun-2026" / "incident.schema.json"
)
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(_SCHEMA)
_VALIDATOR = Draft202012Validator(
    _SCHEMA, format_checker=Draft202012Validator.FORMAT_CHECKER
)


class TrailRunIncidentService:
    """Small service boundary that checks role policy before store operations."""

    def __init__(
        self,
        store: SQLiteIncidentStore,
        *,
        allowed_checkpoint_ids: set[str] | frozenset[str] | None = None,
    ) -> None:
        self._store = store
        # Scope must be supplied by a trusted authentication/authorization adapter.
        # None means no checkpoint access, not unrestricted access.
        self._allowed_checkpoint_ids = frozenset(allowed_checkpoint_ids or ())

    def _require_checkpoint(self, checkpoint_id: str) -> None:
        if checkpoint_id not in self._allowed_checkpoint_ids:
            raise AccessDenied("CHECKPOINT_SCOPE_DENIED")

    def _require_incident_scope(self, incident_id: str) -> dict[str, Any] | None:
        incident = self._store.get_incident(incident_id)
        if incident is None:
            return None
        payload = incident.get("payload")
        if not isinstance(payload, dict) or not isinstance(payload.get("checkpoint_id"), str):
            # Fail closed if stored data is malformed or lacks a scope attribute.
            raise AccessDenied("INCIDENT_SCOPE_METADATA_MISSING")
        self._require_checkpoint(payload["checkpoint_id"])
        return incident

    @staticmethod
    def _require(role: str, action: str) -> None:
        decision = authorize(role, action)
        if not decision.allowed:
            raise AccessDenied(decision.reason_code)

    def create_incident(self, role: str, payload: dict[str, Any]):
        self._require(role, "incident:create")
        if not isinstance(payload, dict):
            raise InvalidIncidentPayload("Incident payload must be an object")
        errors = sorted(_VALIDATOR.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.path) or "<root>"
            raise InvalidIncidentPayload(
                f"Incident schema validation failed at {location}: {first.message}"
            )
        checkpoint_id = payload.get("checkpoint_id")
        if not isinstance(checkpoint_id, str) or not checkpoint_id:
            raise InvalidIncidentPayload(
                "checkpoint_id is required for this checkpoint-scoped pilot"
            )
        # Audit history is append-only after creation. Do not accept client-preloaded history.
        if len(payload["audit"]) != 1:
            raise InvalidIncidentPayload(
                "New incidents must contain exactly one initial audit entry"
            )
        if payload.get("reported_by_role") != role:
            raise AccessDenied("REPORTED_BY_ROLE_MISMATCH")
        # Keep the initial audit attribution consistent with the role accepted
        # at this service boundary. This is consistency validation, not identity proof.
        first_audit_entry = payload["audit"][0]
        if first_audit_entry.get("actor_role") != role:
            raise AccessDenied("AUDIT_ACTOR_ROLE_MISMATCH")
        if first_audit_entry.get("action") != "REPORTED":
            raise InvalidIncidentPayload("Initial audit action must be REPORTED")
        self._require_checkpoint(checkpoint_id)
        return self._store.create_incident(payload)

    def get_incident(self, role: str, incident_id: str):
        self._require(role, "incident:read")
        return self._require_incident_scope(incident_id)

    def get_audit(self, role: str, incident_id: str):
        self._require(role, "audit:read")
        self._require_incident_scope(incident_id)
        return self._store.get_audit(incident_id)

    def transition(
        self,
        role: str,
        incident_id: str,
        requested_status: str,
        *,
        at: str,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        decision = authorize_transition(role, requested_status)
        if not decision.allowed:
            raise AccessDenied(decision.reason_code)
        self._require_incident_scope(incident_id)
        return self._store.transition(
            incident_id,
            requested_status,
            actor_role=role,
            at=at,
            correlation_id=correlation_id,
        )
