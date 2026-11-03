"""Privacy-minimizing observable learning evidence contracts; no psychological diagnosis."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from enum import Enum
import re
from typing import Any

class AssistanceLevel(str, Enum):
    NONE = "none"
    HINT = "hint"
    FEEDBACK = "feedback"
    FULL_SOLUTION = "full_solution"

class TaskRisk(str, Enum):
    LOW = "low"
    ELEVATED = "elevated"
    HIGH = "high"

class EngagementStatus(str, Enum):
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    ENGAGEMENT_EVIDENCE_PRESENT = "engagement_evidence_present"
    REVIEW_RECOMMENDED = "review_recommended"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"

def _validate_score(value: float | None, name: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number or None")
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0")

@dataclass(frozen=True)
class LearningEvidence:
    """One task/session record. learner_ref uses a constrained pseudonymous token."""
    evidence_id: str
    learner_ref: str
    task_ref: str
    assistance_level: AssistanceLevel
    task_risk: TaskRisk = TaskRisk.LOW
    planning_observed: bool | None = None
    verification_actions: int | None = None
    reflection_observed: bool | None = None
    task_performance_score: float | None = None
    independent_learning_score: float | None = None
    delayed_retention_score: float | None = None

    def __post_init__(self) -> None:
        for name in ("evidence_id", "learner_ref", "task_ref"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not re.fullmatch(r"learner-[A-Za-z0-9_-]{1,64}", self.learner_ref):
            raise ValueError("learner_ref must use the pseudonymous learner-<token> format")
        if not isinstance(self.assistance_level, AssistanceLevel):
            raise TypeError("assistance_level must be an AssistanceLevel")
        if not isinstance(self.task_risk, TaskRisk):
            raise TypeError("task_risk must be a TaskRisk")
        for name in ("planning_observed", "reflection_observed"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, bool):
                raise TypeError(f"{name} must be bool or None")
        if self.verification_actions is not None:
            if isinstance(self.verification_actions, bool) or not isinstance(self.verification_actions, int):
                raise TypeError("verification_actions must be an integer or None")
            if self.verification_actions < 0:
                raise ValueError("verification_actions cannot be negative")
        for name in ("task_performance_score", "independent_learning_score", "delayed_retention_score"):
            _validate_score(getattr(self, name), name)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["assistance_level"] = self.assistance_level.value
        data["task_risk"] = self.task_risk.value
        return data

@dataclass(frozen=True)
class LearningEvaluation:
    evidence_id: str
    engagement_status: EngagementStatus
    task_performance_score: float | None
    independent_learning_score: float | None
    delayed_retention_score: float | None
    reasons: tuple[str, ...]
    recommended_next_step: str
    requires_human_review: bool

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["engagement_status"] = self.engagement_status.value
        data["reasons"] = list(self.reasons)
        return data
