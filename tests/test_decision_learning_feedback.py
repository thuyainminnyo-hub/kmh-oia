import unittest

from src.adaptation_engine import AdaptationEngine
from src.decision_learning_feedback import DecisionLearningFeedbackEngine
from src.decision_outcome_evaluator import DecisionOutcome
from src.operating_memory import OperatingMemory


class DecisionLearningFeedbackTests(unittest.TestCase):
    def outcome(self, quality="GOOD"):
        return DecisionOutcome("decision:1", "cmd:1", quality == "GOOD", quality, "verified outcome")

    def test_good_decision_is_recorded_without_adaptation(self):
        memory = OperatingMemory()
        result = DecisionLearningFeedbackEngine().capture(
            self.outcome(), memory=memory, wanted="review risk",
            actual="risk reduced", next_command="continue"
        )
        self.assertEqual(result.memory.decision, "Decision decision:1: GOOD")
        self.assertIsNone(result.adaptation)

    def test_poor_decision_creates_proposed_adaptation(self):
        memory = OperatingMemory()
        result = DecisionLearningFeedbackEngine().capture(
            self.outcome("POOR"), memory=memory, wanted="review risk",
            actual="risk increased", next_command="revise rule",
            adaptation_engine=AdaptationEngine(),
            proposed_change="Change risk review rule",
            expected_effect="Reduce repeated risk",
            next_experiment="Run revised review",
        )
        self.assertIsNotNone(result.adaptation)
        self.assertEqual(result.adaptation.status, "PROPOSED")
        self.assertEqual(result.adaptation.source_command_id, "cmd:1")

    def test_feedback_never_auto_applies_adaptation(self):
        result = DecisionLearningFeedbackEngine().capture(
            self.outcome("POOR"), memory=OperatingMemory(),
            wanted="review", actual="bad", next_command="revise"
        )
        self.assertEqual(result.adaptation.status, "PROPOSED")


if __name__ == "__main__":
    unittest.main()
