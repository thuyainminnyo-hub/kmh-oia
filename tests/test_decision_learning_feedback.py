import unittest

from src.decision_learning_feedback import DecisionLearningFeedbackEngine
from src.decision_outcome_evaluator import DecisionOutcome
from src.operating_memory import OperatingMemory


class DecisionLearningFeedbackTests(unittest.TestCase):
    def outcome(self, quality="GOOD", decision_id="decision:1", command_id="cmd:1"):
        return DecisionOutcome(
            decision_id,
            command_id,
            quality == "GOOD",
            quality,
            "Caller-supplied outcome evaluation; external verification is not established.",
        )

    def test_good_unverified_decision_is_only_provisional_observation(self):
        result = DecisionLearningFeedbackEngine().capture(
            self.outcome(), memory=OperatingMemory(), wanted="review risk",
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
            next_command="revise rule",
        )
        self.assertIsNone(result.adaptation)
        self.assertIn("Hold adaptation proposal creation", result.memory.changed)

    def test_caller_injected_admission_object_is_rejected(self):
        class CallerClaim:
            decision_id = "decision:1"
            command_id = "cmd:1"

        with self.assertRaisesRegex(ValueError, "caller-supplied admission objects are not trusted"):
            DecisionLearningFeedbackEngine().capture(
                self.outcome("POOR"), memory=OperatingMemory(),
                wanted="review risk", actual="bad result",
                next_command="hold", admission=CallerClaim(),
            )

    def test_feedback_never_auto_applies_or_creates_adaptation(self):
        result = DecisionLearningFeedbackEngine().capture(
            self.outcome("POOR"), memory=OperatingMemory(),
            wanted="review", actual="bad", next_command="hold",
        )
        self.assertIsNone(result.adaptation)


if __name__ == "__main__":
    unittest.main()
