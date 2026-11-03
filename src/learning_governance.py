"""Evidence-gated learning proposal review. This module never mutates live policy."""
from dataclasses import dataclass
from enum import Enum
from src.evidence_admission_gate import EvidenceAdmissionResult

class RootCause(str, Enum):
    NONE = "none"
    PROMPT_OR_CONTEXT = "prompt_or_context"
    MODEL_OUTPUT = "model_output"
    ROUTING_OR_BUDGET = "routing_or_budget"
    TOOL_OR_EXECUTION = "tool_or_execution"
    DATA_OR_PROVENANCE = "data_or_provenance"
    POLICY_OR_GUARDRAIL = "policy_or_guardrail"
    UNKNOWN = "unknown"

class LearningDecision(str, Enum):
    HOLD = "HOLD"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED_FOR_PROMOTION = "APPROVED_FOR_PROMOTION"

@dataclass(frozen=True)
class RegressionEvidence:
    suite_id: str
    baseline_passed: bool
    candidate_passed: bool
    cases_total: int
    cases_failed: int
    def __post_init__(self):
        if not isinstance(self.suite_id, str) or not self.suite_id.strip():
            raise ValueError("suite_id must be non-empty")
        if not isinstance(self.baseline_passed, bool) or not isinstance(self.candidate_passed, bool):
            raise ValueError("regression pass flags must be boolean")
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in (self.cases_total, self.cases_failed)):
            raise ValueError("regression counts must be non-negative integers")
        if self.cases_total == 0 or self.cases_failed > self.cases_total:
            raise ValueError("regression case counts are invalid")

@dataclass(frozen=True)
class LearningCandidate:
    candidate_id: str
    execution_id: str
    decision_id: str
    trace_id: str
    artifact_digest: str
    expected_outcome: str
    actual_outcome: str
    root_cause: RootCause
    proposed_change: str

@dataclass(frozen=True)
class LearningReview:
    candidate: LearningCandidate
    decision: LearningDecision
    reasons: tuple[str, ...]
    regression_suite_id: str | None
    owner_approval_id: str | None

class EvidenceGatedLearningReviewer:
    """Assess a proposal; promotion remains a separate governed operation."""
    def review(self, candidate, admission, regression, *, owner_approval_id=None):
        if not isinstance(candidate, LearningCandidate):
            raise ValueError("candidate must be a LearningCandidate")
        if not isinstance(admission, EvidenceAdmissionResult):
            raise ValueError("admission must be an EvidenceAdmissionResult")
        fields = ("candidate_id", "execution_id", "decision_id", "trace_id", "artifact_digest", "expected_outcome", "actual_outcome", "proposed_change")
        missing = [name for name in fields if not isinstance(getattr(candidate, name), str) or not getattr(candidate, name).strip()]
        if missing:
            raise ValueError("candidate fields are missing: " + ", ".join(missing))
        if not isinstance(candidate.root_cause, RootCause):
            raise ValueError("root_cause must be a RootCause")
        reasons = []
        if not admission.learning_admitted or admission.decision != "ADMITTED" or admission.evidence_status != "OUTCOME_LINKED":
            reasons.append("Trusted outcome-linked evidence is not admitted.")
        if regression is None:
            reasons.append("Independent regression evidence is missing.")
        elif not regression.baseline_passed:
            reasons.append("Baseline regression suite did not pass.")
        elif not regression.candidate_passed or regression.cases_failed:
            reasons.append("Candidate regression suite did not pass cleanly.")
        if reasons:
            return LearningReview(candidate, LearningDecision.HOLD, tuple(reasons), regression.suite_id if regression else None, None)
        if not isinstance(owner_approval_id, str) or not owner_approval_id.strip():
            return LearningReview(candidate, LearningDecision.REVIEW_REQUIRED, ("Evidence and regression passed; explicit owner approval is required. No live policy was changed.",), regression.suite_id, None)
        return LearningReview(candidate, LearningDecision.APPROVED_FOR_PROMOTION, ("Approval recorded for a separate governed promotion step; this review does not mutate active policy.",), regression.suite_id, owner_approval_id)
