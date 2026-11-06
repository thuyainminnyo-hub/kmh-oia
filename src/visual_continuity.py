"""Deterministic, evidence-backed continuity gate for KMH OIA.

This module evaluates scores supplied by a pluggable vision/human evaluator.
It does NOT perform image recognition or claim that numeric similarity proves identity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Mapping, Protocol
from uuid import uuid4


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
        if not self.version.strip():
            raise ValueError("policy version must not be empty")
        for name, threshold in self.thresholds.items():
            if not name.strip() or not 0.0 <= threshold <= 1.0:
                raise ValueError(f"invalid threshold for {name!r}")
        missing = set(self.required_dimensions) - set(self.thresholds)
        if missing:
            raise ValueError(f"missing thresholds for required dimensions: {sorted(missing)}")


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
    evidence_uris: tuple[str, ...] = ()
    human_review_required: bool = True

    def __post_init__(self) -> None:
        for field_name in ("film_id", "scene_id", "shot_id", "generated_asset_id",
                           "evaluator", "evaluator_version"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if not self.reference_asset_ids:
            raise ValueError("at least one reference_asset_id is required")
        for name, score in self.scores.items():
            if not name.strip() or not 0.0 <= score <= 1.0:
                raise ValueError(f"score for {name!r} must be between 0 and 1")


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
