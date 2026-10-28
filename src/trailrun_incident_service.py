"""Authorization-enforcing service boundary for the TGiTrailRun pilot.

The caller must authenticate the user and derive role from a trusted identity
provider before constructing/using this service. This module does not implement
authentication, runner/resource scoping, network transport, or dispatch.
"""
from __future__ import annotations

from typing import Any

from src.trailrun_incident_access import authorize, authorize_transition
from src.trailrun_incident_store import (
    IncidentStoreError,
    InvalidTransition,
    SQLiteIncidentStore,
)


class AccessDenied(PermissionError):
    """Raised when a trusted caller role lacks permission for an action."""


class TrailRunIncidentService:
    """Small service boundary that checks role policy before store operations."""

    def __init__(self, store: SQLiteIncidentStore) -> None:
        self._store = store

    @staticmethod
    def _require(role: str, action: str) -> None:
        decision = authorize(role, action)
        if not decision.allowed:
            raise AccessDenied(decision.reason_code)

    def create_incident(self, role: str, payload: dict[str, Any]):
        self._require(role, "incident:create")
        if payload.get("reported_by_role") != role:
            raise AccessDenied("REPORTED_BY_ROLE_MISMATCH")
        return self._store.create_incident(payload)

    def get_incident(self, role: str, incident_id: str):
        self._require(role, "incident:read")
        return self._store.get_incident(incident_id)

    def get_audit(self, role: str, incident_id: str):
        self._require(role, "audit:read")
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
        return self._store.transition(
            incident_id,
            requested_status,
            actor_role=role,
            at=at,
            correlation_id=correlation_id,
        )
