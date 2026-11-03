"""Provider-neutral EduAutomate learning evidence contract adapter.

This validates a proposed normalized contract only. It performs no HTTP,
authentication, persistence, or live EduAutomate API calls.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any, Mapping
from src.human_intelligence import AssistanceLevel, LearningEvidence, TaskRisk

CONTRACT_VERSION = "1.0"
_REQUIRED = {"contract_version", "source_record_ref", "course_ref", "lesson_ref", "observed_at", "evidence"}
_ALLOWED_EVIDENCE = {"evidence_id", "learner_ref", "task_ref", "assistance_level", "task_risk", "planning_observed", "verification_actions", "reflection_observed", "task_performance_score", "independent_learning_score", "delayed_retention_score"}
_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

class ContractValidationError(ValueError):
    """Raised when an inbound normalized record violates the contract."""

@dataclass(frozen=True)
class AdaptedLearningRecord:
    source_record_ref: str
    course_ref: str
    lesson_ref: str
    observed_at: str
    evidence: LearningEvidence

def _required_ref(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not _REF.fullmatch(value):
        raise ContractValidationError(f"{field} must be a non-empty opaque reference")
    return value

def _utc_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError("observed_at must be an ISO-8601 timestamp")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ContractValidationError("observed_at must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractValidationError("observed_at must include a timezone")
    return parsed.isoformat()

def adapt_learning_record(payload: Mapping[str, Any]) -> AdaptedLearningRecord:
    """Validate a normalized record and map it to the existing evidence model.

    Unknown fields are rejected to prevent accidental PII or provider-field ingestion.
    Missing measurements remain None and are never interpreted as negative results.
    """
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")
    unknown, missing = set(payload) - _REQUIRED, _REQUIRED - set(payload)
    if missing:
        raise ContractValidationError(f"missing required fields: {", ".join(sorted(missing))}")
    if unknown:
        raise ContractValidationError(f"unknown top-level fields: {", ".join(sorted(unknown))}")
    if payload["contract_version"] != CONTRACT_VERSION:
        raise ContractValidationError("unsupported contract_version")
    raw = payload["evidence"]
    if not isinstance(raw, Mapping):
        raise ContractValidationError("evidence must be an object")
    unknown_evidence, missing_evidence = set(raw) - _ALLOWED_EVIDENCE, _ALLOWED_EVIDENCE - set(raw)
    if missing_evidence:
        raise ContractValidationError(f"missing evidence fields: {", ".join(sorted(missing_evidence))}")
    if unknown_evidence:
        raise ContractValidationError(f"unknown evidence fields: {", ".join(sorted(unknown_evidence))}")
    try:
        evidence = LearningEvidence(
            evidence_id=raw["evidence_id"], learner_ref=raw["learner_ref"], task_ref=raw["task_ref"],
            assistance_level=AssistanceLevel(raw["assistance_level"]), task_risk=TaskRisk(raw["task_risk"]),
            planning_observed=raw["planning_observed"], verification_actions=raw["verification_actions"],
            reflection_observed=raw["reflection_observed"], task_performance_score=raw["task_performance_score"],
            independent_learning_score=raw["independent_learning_score"], delayed_retention_score=raw["delayed_retention_score"],
        )
    except (TypeError, ValueError, KeyError) as exc:
        raise ContractValidationError(f"invalid learning evidence: {type(exc).__name__}") from exc
    return AdaptedLearningRecord(
        source_record_ref=_required_ref(payload, "source_record_ref"),
        course_ref=_required_ref(payload, "course_ref"), lesson_ref=_required_ref(payload, "lesson_ref"),
        observed_at=_utc_timestamp(payload["observed_at"]), evidence=evidence,
    )