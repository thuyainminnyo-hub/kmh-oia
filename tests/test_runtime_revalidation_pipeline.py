import unittest

from src.runtime_revalidation_pipeline import RuntimeRevalidationPipeline
from src.standardization_engine import OperatingStandard


class RuntimeRevalidationPipelineTests(unittest.TestCase):
    def test_no_drift_does_not_trigger_revalidation(self):
        standard = OperatingStandard("std:a:v1", "a", "Require evidence", "Quality", 1, "ACTIVE")
        result = RuntimeRevalidationPipeline().process(
            standard,
            "cmd:1",
            applied_rule="Require evidence",
            evidence_id="trace:1",
            observed_effect=1.0,
            outcome_positive=True,
        )
        self.assertFalse(result.revalidated)
        self.assertIsNone(result.control_result.trigger)

    def test_drift_automatically_runs_revalidation(self):
        standard = OperatingStandard("std:a:v1", "a", "Require evidence", "Quality", 1, "ACTIVE")
        result = RuntimeRevalidationPipeline().process(
            standard,
            "cmd:2",
            applied_rule="Skip evidence",
            evidence_id="trace:2",
            observed_effect=1.0,
            outcome_positive=True,
        )
        self.assertTrue(result.revalidated)
        self.assertIsNotNone(result.control_result.trigger)
        self.assertIsNotNone(result.control_result.revalidation)
        self.assertEqual(result.control_result.revalidation.revalidation.verdict, "VALID")

    def test_revalidation_can_produce_revision_without_auto_activation(self):
        standard = OperatingStandard("std:a:v1", "a", "Require evidence", "Quality", 1, "ACTIVE")
        result = RuntimeRevalidationPipeline().process(
            standard,
            "cmd:3",
            applied_rule="Skip evidence",
            evidence_id="trace:3",
            observed_effect=0.0,
            outcome_positive=False,
        )
        run = result.control_result.revalidation
        self.assertEqual(run.revalidation.verdict, "REVISE")
        self.assertEqual(run.lifecycle.action, "REVISE")
        self.assertEqual(standard.status, "ACTIVE")


if __name__ == "__main__":
    unittest.main()
