import unittest
from src.human_intelligence import AssistanceLevel, EngagementStatus, LearningEvidence, TaskRisk, evaluate_learning_evidence

def make_evidence(**overrides):
    values = dict(
        evidence_id="ev-001", learner_ref="learner-pseudo-001",
        task_ref="python-function-debugging", assistance_level=AssistanceLevel.HINT,
        task_risk=TaskRisk.LOW, planning_observed=True, verification_actions=2,
        reflection_observed=True, task_performance_score=0.9,
        independent_learning_score=0.8, delayed_retention_score=0.7,
    )
    values.update(overrides)
    return LearningEvidence(**values)

class TestHumanIntelligenceEngine(unittest.TestCase):
    def test_positive_observable_evidence(self):
        result = evaluate_learning_evidence(make_evidence())
        self.assertEqual(result.engagement_status, EngagementStatus.ENGAGEMENT_EVIDENCE_PRESENT)
        self.assertEqual(result.task_performance_score, 0.9)
        self.assertEqual(result.independent_learning_score, 0.8)
        self.assertFalse(result.requires_human_review)

    def test_missing_values_are_unknown_not_negative(self):
        result = evaluate_learning_evidence(make_evidence(
            planning_observed=None, verification_actions=None, reflection_observed=None))
        self.assertEqual(result.engagement_status, EngagementStatus.INSUFFICIENT_EVIDENCE)

    def test_multiple_observed_absences_recommend_guidance(self):
        result = evaluate_learning_evidence(make_evidence(
            planning_observed=False, verification_actions=0, reflection_observed=False))
        self.assertEqual(result.engagement_status, EngagementStatus.REVIEW_RECOMMENDED)
        self.assertIn("without_labeling_the_learner", result.recommended_next_step)

    def test_high_risk_requires_human_review(self):
        result = evaluate_learning_evidence(make_evidence(task_risk=TaskRisk.HIGH))
        self.assertEqual(result.engagement_status, EngagementStatus.HUMAN_APPROVAL_REQUIRED)
        self.assertTrue(result.requires_human_review)

    def test_performance_and_learning_scores_are_separate(self):
        result = evaluate_learning_evidence(make_evidence(
            task_performance_score=1.0, independent_learning_score=0.2))
        self.assertEqual(result.task_performance_score, 1.0)
        self.assertEqual(result.independent_learning_score, 0.2)

    def test_score_range_is_enforced(self):
        with self.assertRaises(ValueError):
            make_evidence(independent_learning_score=1.1)

    def test_negative_verification_count_is_rejected(self):
        with self.assertRaises(ValueError):
            make_evidence(verification_actions=-1)

    def test_email_like_learner_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            make_evidence(learner_ref="student@example.com")

    def test_serialization_uses_enum_values(self):
        payload = make_evidence().to_dict()
        self.assertEqual(payload["assistance_level"], "hint")
        self.assertEqual(payload["task_risk"], "low")

    def test_missing_independent_and_delayed_scores_are_explicit(self):
        result = evaluate_learning_evidence(make_evidence(
            independent_learning_score=None, delayed_retention_score=None))
        self.assertIn("independent_learning_not_measured", result.reasons)
        self.assertIn("delayed_retention_not_measured", result.reasons)

if __name__ == "__main__":
    unittest.main()
