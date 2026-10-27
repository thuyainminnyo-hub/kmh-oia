"""Typed, side-effect-free contract for future asset-scoped remediation execution.

This module deliberately does not execute commands or integrate with the live
runtime. The bridge remains fail-closed until a trusted resolver, executor,
audit sink, and independent verifier are implemented and reviewed.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


EXECUTABLE_ACTIONS = frozenset({"mitigate", "remediate", "monitor", "escalate"})


def _require_nonblank(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_aware(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")


class RemediationStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RemediationRequest:
    """Validated immutable request; construction does not authorize or execute."""

    command_id: str
    case_id: str
    registry_version: int
    asset_id: str
    action: str
    approval_id: str
    idempotency_key: str
    requested_at: datetime

    def __post_init__(self) -> None:
        for name in (
            "command_id", "case_id", "asset_id", "approval_id", "idempotency_key"
        ):
            _require_nonblank(getattr(self, name), name)
        if not isinstance(self.registry_version, int) or isinstance(self.registry_version, bool) or self.registry_version < 1:
            raise ValueError("registry_version must be a positive integer")
        if self.action not in EXECUTABLE_ACTIONS:
            raise ValueError("action is not an allowed cybersecurity action")
        _require_aware(self.requested_at, "requested_at")


@dataclass(frozen=True)
class RemediationResult:
    """Structured executor observation; not proof of independent verification."""

    execution_id: str
    command_id: str
    case_id: str
    registry_version: int
    asset_id: str
    action: str
    executor_id: str
    target_id: str
    started_at: datetime
    finished_at: datetime
    status: RemediationStatus
    before_evidence_refs: tuple[str, ...] = ()
    action_evidence_refs: tuple[str, ...] = ()
    after_evidence_refs: tuple[str, ...] = ()
    rollback_evidence_refs: tuple[str, ...] = ()
    error_code: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "execution_id", "command_id", "case_id", "asset_id",
            "executor_id", "target_id",
        ):
            _require_nonblank(getattr(self, name), name)
        if not isinstance(self.registry_version, int) or isinstance(self.registry_version, bool) or self.registry_version < 1:
            raise ValueError("registry_version must be a positive integer")
        if self.action not in EXECUTABLE_ACTIONS:
            raise ValueError("action is not an allowed cybersecurity action")
        if not isinstance(self.status, RemediationStatus):
            raise ValueError("status must be a RemediationStatus value")
        _require_aware(self.started_at, "started_at")
        _require_aware(self.finished_at, "finished_at")
        if self.finished_at < self.started_at:
            raise ValueError("finished_at must not precede started_at")
        for name in (
            "before_evidence_refs", "action_evidence_refs",
            "after_evidence_refs", "rollback_evidence_refs",
        ):
            refs = getattr(self, name)
            if not isinstance(refs, tuple) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
                raise ValueError(f"{name} must be a tuple of non-empty strings")
        if self.status in {RemediationStatus.FAILED, RemediationStatus.PARTIAL, RemediationStatus.UNKNOWN}:
            _require_nonblank(self.error_code or "", "error_code")
