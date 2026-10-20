import unittest

from src.adaptation_engine import AdaptationEngine
from src.decision_learning_feedback import DecisionLearningFeedbackEngine
from src.decision_outcome_evaluator import DecisionOutcome
from src.evidence_admission_gate import EvidenceAdmissionResult
from src.live_runtime_bridge import ExecutionRecord
from src.operating_loop_record import OperatingLoopRecord
from src.operating_memory import OperatingMemory
from src.trusted_source_receipt import ReceiptVerificationResult
from src.verified_learning_admission import VerifiedLearningAdmission


class DecisionLearningFeedbackTests(unittest.TestCase):
    def outcome(self, quality="GOOD", decision_id="decision:1", command_id="cmd:1"):
        return DecisionOutcome(
            decision_id,
            command_id,
            quality == "GOOD",
            quality,
            "Caller-supplied outcome evaluation; external verification is not established.",
        )

    def execution(self):
        loop = OperatingLoopRecord(
            context_id="context:1",
            decision_id="decision:1",
            command_id="cmd:1",
            execution_id="exec:1",
            trace_id="trace:1",
            qa_status="PASS",
            evidence_status="OUTCOME_LINKED",
            learning_status="ADMITTED",
            source_decision_id="decision:1",
        )
        admission = EvidenceAdmissionResult(
            decision="ADMITTED",
            evidence_status="OUTCOME_LINKED",
            learning_admitted=True,
            missing_fields=(),
            reasons=("trusted receipt matched execution and outcome linkage",),
        )
        receipt = ReceiptVerificationResult(
            verified=True,
            provider_name="booking-provider",
            source_record_id="record:1",
            execution_id="exec:1",
            raw_observation="booking=confirmed",
            verification_method="test-adapter",
            reasons=("test receipt accepted",),
        )
        return ExecutionRecord(
            command_id="cmd:1",
            response="done",
            trace_stages=("input_gateway", "evaluation"),
            evidence=("trace_id=trace:1",),
            qa_status="PASS",
            final_status="LEARNED",
            source_decision_id="decision:1",
            operating_loop=loop,
            admission=admission,
            trusted_receipt_verification=receipt,
        )

    def verified_admission(self, quality="POOR"):
        return VerifiedLearningAdmission.from_execution(
            self.outcome(quality), self.execution(),
            evidence_id="evidence:1",
            policy_version="policy:v1",
        )

    def test_good_unverified_decision_is_only_provisional_observation(self):
        memory = OperatingMemory()
        result = DecisionLearningFeedbackEngine().capture(
            self.outcome(), memory=memory, wanted="review risk",
            actual="risk reduced", next_command="continue"
        )
        self.assertEqual(result.memory.decision, "Decision decision:1: GOOD")
        self.assertIn("not established", result.memory.verified)
        self.assertIn("provisional observation only", result.memory.learned)
        self.assertIsNone(result.adaptation)
        self.assertIsNone(result.admission)

    def test_poor_unverified_decision_does_not_create_adaptation(self):
        result = DecisionLearningFeedbackEngine().capture(
            self.outcome("POOR"), memory=OperatingMemory(),
            wanted="review risk", actual="risk increased",
            next_command="revise rule", adaptation_engine=AdaptationEngine(),
        )
        self.assertIsNone(result.adaptation)
        self.assertIn("Hold adaptation proposal creation", result.memory.changed)

    def test_poor_admitted_outcome_creates_proposal_not_application(self):
        result = DecisionLearningFeedbackEngine().capture(
            self.outcome("POOR"), memory=OperatingMemory(),
            wanted="review risk", actual="risk increased",
            next_command="revise rule",
            adaptation_engine=AdaptationEngine(),
            proposed_change="Change risk review rule",
            expected_effect="Reduce repeated risk",
            next_experiment="Run revised review",
            admission=self.verified_admission(),
        )
        self.assertIsNotNone(result.adaptation)
        self.assertEqual(result.adaptation.status, "PROPOSED")
        self.assertEqual(result.adaptation.source_command_id, "cmd:1")
        self.assertIn("Trusted source receipt passed", result.memory.verified)
        self.assertEqual(result.admission.execution_id, "exec:1")

    def test_good_admitted_outcome_does_not_create_adaptation(self):
        result = DecisionLearningFeedbackEngine().capture(
            self.outcome("GOOD"), memory=OperatingMemory(),
            wanted="review risk", actual="risk reduced",
            next_command="continue", admission=self.verified_admission("GOOD"),
        )
        self.assertIsNone(result.adaptation)
        self.assertIn("outcome-linked evidence was admitted", result.memory.learned.lower())

    def test_admission_for_different_outcome_is_rejected(self):
        proof = self.verified_admission()
        with self.assertRaisesRegex(ValueError, "does not match"):
            DecisionLearningFeedbackEngine().capture(
                self.outcome("POOR", decision_id="decision:other"),
                memory=OperatingMemory(), wanted="review", actual="bad",
                next_command="revise", admission=proof,
            )

    def test_feedback_never_auto_applies_adaptation(self):
        result = DecisionLearningFeedbackEngine().capture(
            self.outcome("POOR"), memory=OperatingMemory(),
            wanted="review", actual="bad", next_command="revise",
            admission=self.verified_admission(),
        )
        self.assertEqual(result.adaptation.status, "PROPOSED")


if __name__ == "__main__":
    unittest.main()
