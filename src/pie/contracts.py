"""Versioned, immutable data contracts for the first synthetic PIE increment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Any


class ContractError(ValueError):
    """Raised when a PIE contract is malformed or violates a safety invariant."""


class Environment(str, Enum):
    LOCAL_SYNTHETIC = "local_synthetic"
    ISOLATED_CLOUD_SANDBOX = "isolated_cloud_sandbox"


class ProjectStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"


class RequirementType(str, Enum):
    FUNCTIONAL = "Functional"
    NON_FUNCTIONAL = "Non-functional"
    SECURITY = "Security"


class RequirementPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


_PROJECT_ID = re.compile(r"^PRJ-[0-9]{3}$")
_REQUIREMENT_ID = re.compile(r"^REQ-[0-9]{3,}$")
_PAC_ID = re.compile(r"^PAC-PRJ-[0-9]{3}-[0-9]{3}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _required_text(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a non-empty string")


def _identifier(name: str, value: Any, pattern: re.Pattern[str], expected: str) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ContractError(f"{name} must match {expected}")


def _immutable_text_tuple(name: str, value: Any, *, required: bool) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ContractError(f"{name} must be a list or tuple of strings")
    normalized = tuple(value)
    if required and not normalized:
        raise ContractError(f"{name} must contain at least one item")
    if any(not isinstance(item, str) or not item.strip() for item in normalized):
        raise ContractError(f"{name} items must be non-empty strings")
    return normalized


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProjectBrief:
    project_id: str
    brief_version: int
    project_name: str
    objective: str
    scope: tuple[str, ...]
    non_goals: tuple[str, ...]
    requested_environment: str
    effective_environment: Environment
    created_by: str
    status: ProjectStatus = ProjectStatus.DRAFT
    approval_ref: str | None = None
    content_hash: str = ""

    def __post_init__(self) -> None:
        _identifier("project_id", self.project_id, _PROJECT_ID, "PRJ-NNN")
        if not isinstance(self.brief_version, int) or isinstance(self.brief_version, bool) or self.brief_version < 1:
            raise ContractError("brief_version must be a positive integer")
        for name in ("project_name", "objective", "requested_environment", "created_by"):
            _required_text(name, getattr(self, name))

        # Frozen dataclasses are shallow: normalize caller-owned collections before hashing.
        object.__setattr__(self, "scope", _immutable_text_tuple("scope", self.scope, required=True))
        object.__setattr__(self, "non_goals", _immutable_text_tuple("non_goals", self.non_goals, required=False))

        if not isinstance(self.effective_environment, Environment):
            raise ContractError("effective_environment must be a supported synthetic environment")
        if not isinstance(self.status, ProjectStatus):
            raise ContractError("status must be a supported ProjectStatus")
        if self.status in (ProjectStatus.APPROVED, ProjectStatus.ACTIVE) and not self.approval_ref:
            raise ContractError("APPROVED or ACTIVE briefs require an approval_ref")
        if self.approval_ref is not None:
            _required_text("approval_ref", self.approval_ref)
        if not isinstance(self.content_hash, str):
            raise ContractError("content_hash must be a string")

        expected = _canonical_hash(self.hash_payload())
        if self.content_hash and not _SHA256.fullmatch(self.content_hash):
            raise ContractError("content_hash must be a lowercase SHA-256 digest")
        if self.content_hash and self.content_hash != expected:
            raise ContractError("content_hash does not match canonical brief content")
        if not self.content_hash:
            object.__setattr__(self, "content_hash", expected)

    def hash_payload(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "brief_version": self.brief_version,
            "project_name": self.project_name,
            "objective": self.objective,
            "scope": list(self.scope),
            "non_goals": list(self.non_goals),
            "requested_environment": self.requested_environment,
            "effective_environment": self.effective_environment.value,
            "created_by": self.created_by,
            "status": self.status.value,
            "approval_ref": self.approval_ref,
        }


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    project_id: str
    description: str
    requirement_type: RequirementType
    priority: RequirementPriority
    source_ref: str
    version: int = 1
    status: str = "DRAFT"

    def __post_init__(self) -> None:
        _identifier("requirement_id", self.requirement_id, _REQUIREMENT_ID, "REQ-NNN")
        _identifier("project_id", self.project_id, _PROJECT_ID, "PRJ-NNN")
        for name in ("description", "source_ref", "status"):
            _required_text(name, getattr(self, name))
        if not isinstance(self.requirement_type, RequirementType):
            raise ContractError("requirement_type is invalid")
        if not isinstance(self.priority, RequirementPriority):
            raise ContractError("priority is invalid")
        if not isinstance(self.version, int) or isinstance(self.version, bool) or self.version < 1:
            raise ContractError("version must be a positive integer")


@dataclass(frozen=True)
class AcceptanceCriterion:
    acceptance_id: str
    project_id: str
    requirement_ids: tuple[str, ...]
    acceptance_rule: str
    criticality: str
    verification_method: str
    version: int = 1

    def __post_init__(self) -> None:
        _identifier("acceptance_id", self.acceptance_id, _PAC_ID, "PAC-PRJ-NNN-NNN")
        _identifier("project_id", self.project_id, _PROJECT_ID, "PRJ-NNN")
        if not self.acceptance_id.startswith(f"PAC-{self.project_id}-"):
            raise ContractError("acceptance_id project segment must match project_id")
        normalized_ids = _immutable_text_tuple("requirement_ids", self.requirement_ids, required=True)
        for requirement_id in normalized_ids:
            _identifier("requirement_id", requirement_id, _REQUIREMENT_ID, "REQ-NNN")
        object.__setattr__(self, "requirement_ids", normalized_ids)
        for name in ("acceptance_rule", "criticality", "verification_method"):
            _required_text(name, getattr(self, name))
        if not isinstance(self.version, int) or isinstance(self.version, bool) or self.version < 1:
            raise ContractError("version must be a positive integer")
