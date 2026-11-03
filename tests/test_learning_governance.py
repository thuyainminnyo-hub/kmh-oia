import unittest
from src.evidence_admission_gate import EvidenceAdmissionResult
from src.learning_governance import (EvidenceGatedLearningReviewer, LearningCandidate, LearningDecision, RegressionEvidence, RootCause)

def candidate(**kw):
    d=dict(candidate_id="learn-1",execution_id="exec-1",decision_id="decision-1",trace_id="trace-1",artifact_digest="sha256:abc",expected_outcome="fewer invalid outputs",actual_outcome="invalid outputs reduced",root_cause=RootCause.MODEL_OUTPUT,proposed_change="tighten schema validation")
    d.update(kw); return LearningCandidate(**d)
def admission(ok=True):
    return EvidenceAdmissionResult("ADMITTED" if ok else "NOT_ADMITTED","OUTCOME_LINKED" if ok else "OBSERVED",ok,(),("test",))
def regression(**kw):
    d=dict(suite_id="reg-v1",baseline_passed=True,candidate_passed=True,cases_total=20,cases_failed=0); d.update(kw); return RegressionEvidence(**d)

class LearningGovernanceTests(unittest.TestCase):
    def setUp(self): self.reviewer=EvidenceGatedLearningReviewer()
    def test_unadmitted_evidence_holds(self): self.assertEqual(self.reviewer.review(candidate(),admission(False),regression()).decision,LearningDecision.HOLD)
    def test_missing_regression_holds(self): self.assertEqual(self.reviewer.review(candidate(),admission(),None).decision,LearningDecision.HOLD)
    def test_failed_candidate_regression_holds(self): self.assertEqual(self.reviewer.review(candidate(),admission(),regression(candidate_passed=False,cases_failed=1)).decision,LearningDecision.HOLD)
    def test_passed_gates_require_owner_approval(self): self.assertEqual(self.reviewer.review(candidate(),admission(),regression()).decision,LearningDecision.REVIEW_REQUIRED)
    def test_approval_only_marks_separate_promotion_eligible(self):
        r=self.reviewer.review(candidate(),admission(),regression(),owner_approval_id="approval-1")
        self.assertEqual(r.decision,LearningDecision.APPROVED_FOR_PROMOTION); self.assertIn("does not mutate",r.reasons[0])
    def test_baseline_failure_holds(self): self.assertEqual(self.reviewer.review(candidate(),admission(),regression(baseline_passed=False)).decision,LearningDecision.HOLD)
    def test_missing_digest_rejected(self):
        with self.assertRaisesRegex(ValueError,"artifact_digest"): self.reviewer.review(candidate(artifact_digest=""),admission(),regression())
    def test_bad_counts_rejected(self):
        with self.assertRaisesRegex(ValueError,"case counts"): regression(cases_total=1,cases_failed=2)

if __name__ == "__main__": unittest.main()
