"""Typed registry models and validation for the Landscape Design Intelligence pilot.

This module is intentionally isolated from the core OIA runtime. It validates
supplied evidence and never infers missing site measurements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from math import isfinite
from typing import Any, Literal, Mapping


class ObservationCategory(str, Enum):
    TOPOGRAPHY = "topography"
    SUN = "sun"
    DRAINAGE = "drainage"
    CLIMATE = "climate"
    VEGETATION = "vegetation"
    ACCESS = "access"
    UTILITIES = "utilities"
    HAZARD = "hazard"


class QAStatus(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    name: str
    site_id: str
    brief_version: str
    status: str
    created_at: str


@dataclass(frozen=True)
class SiteRecord:
    site_id: str
    boundary_ref: str
    area_value: float
    area_unit: str
    jurisdiction: str
    source_refs: tuple[str, ...]
    coordinate_reference: str | None = None


@dataclass(frozen=True)
class ObservationRecord:
    observation_id: str
    site_id: str
    category: ObservationCategory
    value: float | str
    unit: str
    observed_at: str
    source_ref: str
    method: str
    confidence: float
    limitations: str = ""


@dataclass(frozen=True)
class RequirementRecord:
    requirement_id: str
    project_id: str
    statement: str
    priority: Literal["low", "medium", "high", "mandatory"]
    acceptance_test: str
    source_ref: str
    status: str = "open"


@dataclass(frozen=True)
class DesignOptionRecord:
    option_id: str
    project_id: str
    version: str
    concept_ref: str
    rationale: str
    linked_observations: tuple[str, ...]
    assumptions: tuple[str, ...]
    author: str
    created_at: str


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    entity_type: str
    entity_id: str
    artifact_uri: str
    content_hash: str
    source_type: str
    captured_at: str
    provenance: str
    access_class: str


@dataclass(frozen=True)
class QACriterionResult:
    criterion_id: str
    result: Literal["PASS", "HOLD", "FAIL"]
    evidence_refs: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class QAResultRecord:
    qa_id: str
    option_id: str
    rubric_version: str
    criterion_results: tuple[QACriterionResult, ...]
    status: QAStatus
    findings: tuple[str, ...]
    reviewer_role: str
    reviewed_at: str


@dataclass(frozen=True)
class RunEventRecord:
    run_id: str
    event_type: str
    input_refs: tuple[str, ...]
    output_refs: tuple[str, ...]
    policy_version: str
    started_at: str
    finished_at: str
    result: str
    error_code: str = ""


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str
    severity: Literal["error", "warning"] = "error"


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def requires_hold(self) -> bool:
        return bool(self.issues)


AREA_UNITS = frozenset({"m2", "ft2", "ha", "acre"})
# Deliberately small, explicit unit allowlist. Extend only with tests.
OBSERVATION_UNITS = frozenset({
    "m", "ft", "cm", "mm", "%", "deg", "h/day", "hours/day",
    "mm/h", "in/h", "L/s", "m3/s", "C", "F", "mm", "in",
    "count", "category", "boolean",
})
REQUIRED_SITE_FIELDS = (
    "site_id", "boundary_ref", "area_value", "area_unit", "jurisdiction",
    "source_refs",
)
REQUIRED_OBSERVATION_FIELDS = (
    "observation_id", "site_id", "category", "value", "unit",
    "observed_at", "source_ref", "method", "confidence",
)


def _nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_iso_date(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False


def validate_site_payload(payload: Mapping[str, Any]) -> ValidationReport:
    """Validate a site payload without coercing values or inventing defaults."""
    issues: list[ValidationIssue] = []

    for field_name in REQUIRED_SITE_FIELDS:
        if field_name not in payload or payload[field_name] is None:
            issues.append(ValidationIssue(
                "required_field_missing", field_name,
                f"Required field '{field_name}' is missing.",
            ))

    for field_name in ("site_id", "boundary_ref", "jurisdiction"):
        if field_name in payload and not _nonblank(payload[field_name]):
            issues.append(ValidationIssue(
                "required_field_blank", field_name,
                f"Required field '{field_name}' must be a non-empty string.",
            ))

    area_value = payload.get("area_value")
    if area_value is not None:
        if isinstance(area_value, bool) or not isinstance(area_value, (int, float)):
            issues.append(ValidationIssue(
                "invalid_numeric_value", "area_value",
                "area_value must be a finite positive number.",
            ))
        elif not isfinite(float(area_value)) or float(area_value) <= 0:
            issues.append(ValidationIssue(
                "invalid_numeric_value", "area_value",
                "area_value must be a finite positive number.",
            ))

    area_unit = payload.get("area_unit")
    if area_unit is not None and (not isinstance(area_unit, str) or area_unit not in AREA_UNITS):
        issues.append(ValidationIssue(
            "unsupported_unit", "area_unit",
            f"Unsupported area unit {area_unit!r}; expected one of {sorted(AREA_UNITS)}.",
        ))

    source_refs = payload.get("source_refs")
    if source_refs is not None:
        if not isinstance(source_refs, (list, tuple)) or not source_refs:
            issues.append(ValidationIssue(
                "provenance_missing", "source_refs",
                "At least one source reference is required for the site record.",
            ))
        elif any(not _nonblank(ref) for ref in source_refs):
            issues.append(ValidationIssue(
                "provenance_invalid", "source_refs",
                "Every source reference must be a non-empty string.",
            ))

    coordinate_reference = payload.get("coordinate_reference")
    if coordinate_reference is not None and not _nonblank(coordinate_reference):
        issues.append(ValidationIssue(
            "coordinate_reference_invalid", "coordinate_reference",
            "coordinate_reference must be omitted or a non-empty string.",
        ))

    return ValidationReport(tuple(issues))


def validate_observation_payload(payload: Mapping[str, Any]) -> ValidationReport:
    """Validate an observation and its provenance; no missing value is inferred."""
    issues: list[ValidationIssue] = []

    for field_name in REQUIRED_OBSERVATION_FIELDS:
        if field_name not in payload or payload[field_name] is None:
            issues.append(ValidationIssue(
                "required_field_missing", field_name,
                f"Required field '{field_name}' is missing.",
            ))

    for field_name in (
        "observation_id", "site_id", "unit", "source_ref", "method",
    ):
        if field_name in payload and not _nonblank(payload[field_name]):
            issues.append(ValidationIssue(
                "required_field_blank", field_name,
                f"Required field '{field_name}' must be a non-empty string.",
            ))

    category = payload.get("category")
    if category is not None:
        try:
            ObservationCategory(category)
        except (ValueError, TypeError):
            issues.append(ValidationIssue(
                "invalid_category", "category",
                f"Unsupported observation category {category!r}.",
            ))

    value = payload.get("value")
    if value is not None:
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            issues.append(ValidationIssue(
                "invalid_value_type", "value",
                "Observation value must be a number or a non-empty categorical string.",
            ))
        elif isinstance(value, float) and not isfinite(value):
            issues.append(ValidationIssue(
                "invalid_numeric_value", "value",
                "Numeric observation values must be finite.",
            ))
        elif isinstance(value, str) and not value.strip():
            issues.append(ValidationIssue(
                "invalid_value_type", "value",
                "Categorical observation values must be non-empty.",
            ))

    unit = payload.get("unit")
    if unit is not None and (not isinstance(unit, str) or unit not in OBSERVATION_UNITS):
        issues.append(ValidationIssue(
            "unsupported_unit", "unit",
            f"Unsupported observation unit {unit!r}; expected one of {sorted(OBSERVATION_UNITS)}.",
        ))

    confidence = payload.get("confidence")
    if confidence is not None:
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            issues.append(ValidationIssue(
                "invalid_confidence", "confidence",
                "confidence must be a number from 0 to 1.",
            ))
        elif not isfinite(float(confidence)) or not 0 <= float(confidence) <= 1:
            issues.append(ValidationIssue(
                "invalid_confidence", "confidence",
                "confidence must be a finite number from 0 to 1.",
            ))

    observed_at = payload.get("observed_at")
    if observed_at is not None and not _parse_iso_date(observed_at):
        issues.append(ValidationIssue(
            "invalid_observed_at", "observed_at",
            "observed_at must be an ISO date or ISO datetime.",
        ))

    source_ref = payload.get("source_ref")
    if source_ref is not None and not _nonblank(source_ref):
        issues.append(ValidationIssue(
            "provenance_missing", "source_ref",
            "A non-empty source_ref is required; unsupported claims cannot be treated as observations.",
        ))

    return ValidationReport(tuple(issues))
