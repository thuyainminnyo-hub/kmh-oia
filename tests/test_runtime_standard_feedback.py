import unittest

from src.runtime_standard_feedback import RuntimeStandardFeedbackEngine
from src.standardization_engine import OperatingStandard


class RuntimeStandardFeedbackTests(unittest.TestCase):
    def test_matching_runtime_evidence_has_no_drift(self) -> None:
        standard = OperatingStandard("std:a:v1", "a", "Require evidence", "Higher quality", 1, "ACTIVE")
        feedback = RuntimeStandardFeedbackEngine().capture(
            standard, "cmd:1", applied_rule="Require evidence", evidence_id="trace:1"
        )
        self.assertFalse(feedback.control_result.drift.drifted)
        self.assertIsNone(feedback.control_result.trigger)

    def test_drifted_runtime_evidence_triggers_revalidation(self) -> None:
        standard = OperatingStandard("std:a:v1", "a", "Require evidence", "Higher quality", 1, "ACTIVE")
        feedback = RuntimeStandardFeedbackEngine().capture(
            standard, "cmd:2", applied_rule="Skip evidence", evidence_id="trace:2"
        )
        self.assertTrue(feedback.control_result.drift.drifted)
        self.assertIsNotNone(feedback.control_result.trigger)
        self.assertEqual(feedback.control_result.trigger.status, "TRIGGERED")

    def test_evidence_id_is_required(self) -> None:
        standard = OperatingStandard("std:a:v1", "a", "Require evidence", "Higher quality", 1, "ACTIVE")
        with self.assertRaises(ValueError):
            RuntimeStandardFeedbackEngine().capture(
                standard, "cmd:3", applied_rule="Require evidence", evidence_id=""
            )


if __name__ == "__main__":
    unittest.main()
