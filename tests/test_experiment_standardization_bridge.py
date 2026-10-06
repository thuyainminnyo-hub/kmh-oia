import unittest
from src.adaptation_validation import AdaptationValidationEngine
from src.experiment_standardization_bridge import ExperimentStandardizationBridge

class ExperimentStandardizationBridgeTests(unittest.TestCase):
    def setUp(self):
        self.validation = AdaptationValidationEngine()
        self.bridge = ExperimentStandardizationBridge()

    def test_improved_experiment_creates_proposed_standard(self):
        experiment = self.validation.evaluate("adapt-1", 10, 12)
        feedback = self.bridge.feedback(experiment, rule="require evidence", expected_effect="higher verified throughput")
        self.assertEqual(feedback.action, "STANDARD_PROPOSED")
        self.assertIsNotNone(feedback.standard)
        self.assertEqual(feedback.standard.status, "PROPOSED")
        self.assertEqual(feedback.standard.source_adaptation_id, "adapt-1")

    def test_no_improvement_does_not_create_standard(self):
        experiment = self.validation.evaluate("adapt-2", 10, 10)
        feedback = self.bridge.feedback(experiment, rule="require evidence", expected_effect="higher verified throughput")
        self.assertEqual(feedback.action, "LEARN")
        self.assertIsNone(feedback.standard)

    def test_regression_requires_revision(self):
        experiment = self.validation.evaluate("adapt-3", 10, 8)
        feedback = self.bridge.feedback(experiment, rule="require evidence", expected_effect="higher verified throughput")
        self.assertEqual(feedback.action, "REVISE")
        self.assertIsNone(feedback.standard)

if __name__ == "__main__":
    unittest.main()
