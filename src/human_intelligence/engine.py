"""Conservative deterministic evaluation of observable learning evidence."""
from .models import EngagementStatus, LearningEvidence, LearningEvaluation, TaskRisk

def evaluate_learning_evidence(evidence: LearningEvidence) -> LearningEvaluation:
    """Missing evidence remains unknown; status is not a diagnosis or learner label."""
    if not isinstance(evidence, LearningEvidence):
        raise TypeError("evidence must be a LearningEvidence instance")
    observed = all(value is not None for value in (
        evidence.planning_observed, evidence.verification_actions, evidence.reflection_observed
    ))
    positive = (
        evidence.planning_observed is True
        and evidence.verification_actions is not None
        and evidence.verification_actions > 0
        and evidence.reflection_observed is True
    )
    negative_count = sum((
        evidence.planning_observed is False,
        evidence.verification_actions == 0,
        evidence.reflection_observed is False,
    ))
    reasons: list[str] = []
    if evidence.task_risk is TaskRisk.HIGH:
        status = EngagementStatus.HUMAN_APPROVAL_REQUIRED
        human_review = True
        reasons.append("high_risk_task_requires_human_review")
        next_step = "pause_automated_decision_and_request_qualified_human_review"
    elif positive:
        status = EngagementStatus.ENGAGEMENT_EVIDENCE_PRESENT
        human_review = False
        reasons.append("planning_verification_and_reflection_observed")
        next_step = "continue_with_independent_practice_and_delayed_assessment"
    elif observed and negative_count >= 2:
        status = EngagementStatus.REVIEW_RECOMMENDED
        human_review = False
        reasons.append("multiple_observable_engagement_steps_not_recorded")
        next_step = "offer_guided_questions_and_collect_new_evidence_without_labeling_the_learner"
    else:
        status = EngagementStatus.INSUFFICIENT_EVIDENCE
        human_review = False
        reasons.append("insufficient_observable_evidence_to_assess_engagement")
        next_step = "collect_missing_measurements_or_offer_optional_guided_practice"
    if evidence.independent_learning_score is None:
        reasons.append("independent_learning_not_measured")
    if evidence.delayed_retention_score is None:
        reasons.append("delayed_retention_not_measured")
    return LearningEvaluation(
        evidence_id=evidence.evidence_id,
        engagement_status=status,
        task_performance_score=evidence.task_performance_score,
        independent_learning_score=evidence.independent_learning_score,
        delayed_retention_score=evidence.delayed_retention_score,
        reasons=tuple(reasons),
        recommended_next_step=next_step,
        requires_human_review=human_review,
    )
