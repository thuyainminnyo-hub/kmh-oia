"""Deterministic, evidence-backed continuity gate for KMH OIA.

This module evaluates scores supplied by a pluggable vision/human evaluator.
It does NOT perform image recognition or claim that numeric similarity proves identity.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from enum import Enum
import math
from types import MappingProxyType
from typing import Protocol
from uuid import uuid4


def _validate_score(name: object, value: object, label: str) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{label} names must be non-empty strings")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} for {name!r} must be a finite number between 0 and 1")
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} for {name!r} must be a finite number between 0 and 1")


def _validate_non_empty_strings(values: object, field_name: str, *, unique: bool = False) -> None:
    if not isinstance(values, tuple) or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{field_name} must contain only non-empty strings")
    if unique and len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")


class ContinuityStatus(str, Enum):
    PASS = "pass"
    REWORK = "rework"
    REVIEW = "review"


@dataclass(frozen=True)
class ContinuityPolicy:
    """Versioned acceptance policy. Scores are normalized to [0, 1]."""

    version: str = "vcie-policy-v1"
    thresholds: Mapping[str, float] = field(default_factory=lambda: {
        "face_identity": 0.95,
        "costume": 0.90,
        "props": 0.90,
        "environment": 0.90,
        "lighting": 0.85,
    })
    required_dimensions: tuple[str, ...] = (
        "face_identity", "costume", "props", "environment", "lighting"
    )

    def __post_init__(self) -> None:
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("policy version must not be empty")
        if not isinstance(self.thresholds, Mapping):
            raise ValueError("thresholds must be a mapping")
        if not isinstance(self.required_dimensions, tuple) or not self.required_dimensions:
            raise ValueError("required_dimensions must be a non-empty tuple")
        if any(not isinstance(name, str) or not name.strip() for name in self.required_dimensions):
            raise ValueError("required_dimensions must contain non-empty strings")
        if len(set(self.required_dimensions)) != len(self.required_dimensions):
            raise ValueError("required_dimensions must not contain duplicates")

        copied_thresholds = dict(self.thresholds)
        for name, threshold in copied_thresholds.items():
            _validate_score(name, threshold, "threshold")
        missing = set(self.required_dimensions) - set(copied_thresholds)
        if missing:
            raise ValueError(f"missing thresholds for required dimensions: {sorted(missing)}")

        object.__setattr__(self, "thresholds", MappingProxyType(copied_thresholds))


@dataclass(frozen=True)
class ShotEvidence:
    film_id: str
    scene_id: str
    shot_id: str
    reference_asset_ids: tuple[str, ...]
    generated_asset_id: str
    evaluator: str
    evaluator_version: str
    scores: Mapping[str, float]
    evidence_uris: tuple[str, ...]
    human_review_required: bool = True

    def __post_init__(self) -> None:
        for field_name in ("film_id", "scene_id", "shot_id", "generated_asset_id",
                           "evaluator", "evaluator_version"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be empty")

        _validate_non_empty_strings(self.reference_asset_ids, "reference_asset_ids", unique=True)
        _validate_non_empty_strings(self.evidence_uris, "evidence_uris")
        if not isinstance(self.scores, Mapping):
            raise ValueError("scores must be a mapping")
        if not isinstance(self.human_review_required, bool):
            raise ValueError("human_review_required must be a boolean")

        copied_scores = dict(self.scores)
        for name, score in copied_scores.items():
            _validate_score(name, score, "score")
        object.__setattr__(self, "scores", MappingProxyType(copied_scores))


@dataclass(frozen=True)
class DimensionResult:
    dimension: str
    score: float | None
    threshold: float
    passed: bool | None
    evidence_state: str


@dataclass(frozen=True)
class ContinuityReport:
    report_id: str
    film_id: str
    scene_id: str
    shot_id: str
    policy_version: str
    evaluator: str
    evaluator_version: str
    status: ContinuityStatus
    dimensions: tuple[DimensionResult, ...]
    missing_dimensions: tuple[str, ...]
    failed_dimensions: tuple[str, ...]
    evidence_uris: tuple[str, ...]
    human_review_required: bool

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


class ContinuityEvaluator(Protocol):
    def evaluate(self, evidence: ShotEvidence,
                 policy: ContinuityPolicy | None = None) -> ContinuityReport: ...


class RuleBasedContinuityEvaluator:
    """Evaluate externally-produced scores; missing evidence never silently passes."""

    def evaluate(self, evidence: ShotEvidence,
                 policy: ContinuityPolicy | None = None) -> ContinuityReport:
        policy = policy or ContinuityPolicy()
        unexpected = set(evidence.scores) - set(policy.thresholds)
        if unexpected:
            raise ValueError(f"unexpected score dimensions: {sorted(unexpected)}")

        results: list[DimensionResult] = []
        missing: list[str] = []
        failed: list[str] = []

        for dimension in policy.required_dimensions:
            score = evidence.scores.get(dimension)
            threshold = policy.thresholds[dimension]
            if score is None:
                missing.append(dimension)
                results.append(DimensionResult(dimension, None, threshold, None, "missing"))
                continue
            passed = score >= threshold
            if not passed:
                failed.append(dimension)
            results.append(DimensionResult(dimension, score, threshold, passed, "provided"))

        if missing:
            status = ContinuityStatus.REVIEW
        elif failed:
            status = ContinuityStatus.REWORK
        else:
            status = ContinuityStatus.PASS

        return ContinuityReport(
            report_id=f"vcie-{uuid4().hex}",
            film_id=evidence.film_id,
            scene_id=evidence.scene_id,
            shot_id=evidence.shot_id,
            policy_version=policy.version,
            evaluator=evidence.evaluator,
            evaluator_version=evidence.evaluator_version,
            status=status,
            dimensions=tuple(results),
            missing_dimensions=tuple(missing),
            failed_dimensions=tuple(failed),
            evidence_uris=evidence.evidence_uris,
            human_review_required=evidence.human_review_required or status != ContinuityStatus.PASS,
        )
