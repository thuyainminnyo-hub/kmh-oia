import unittest

from src.decision_outcome_evaluator import DecisionOutcomeEvaluator
from src.decision_queue import DecisionItem
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import ExecutionRecord
from src.trace import TraceEvent


class DecisionOutcomeEvaluatorTests(unittest.TestCase):
    def execution(self, status="LEARNED"):
        return ExecutionRecord(
            "cmd:1", "done", ("input_gateway", "evaluation"),
            ("trace_id=t1",), "PASS", status, None, None, None, None, "decision:quality_risk:1"
        )

    def decision(self, status="APPROVED"):
        return DecisionItem(
            "decision:quality_risk:1", "QUALITY_RISK", "HIGH",
            "quality issue", "review quality", "system", status
        )

    def test_positive_outcome_is_good(self):
        result = DecisionOutcomeEvaluator().evaluate(
            self.decision(), self.execution(), outcome_positive=True
        )
        self.assertEqual(result.quality, "GOOD")
        self.assertTrue(result.outcome_positive)

    def test_negative_outcome_is_poor(self):
        result = DecisionOutcomeEvaluator().evaluate(
            self.decision(), self.execution(), outcome_positive=False
        )
        self.assertEqual(result.quality, "POOR")

    def test_pending_decision_cannot_be_evaluated(self):
        with self.assertRaises(ValueError):
            DecisionOutcomeEvaluator().evaluate(
                self.decision("PENDING"), self.execution(), outcome_positive=True
            )

    def test_unlearned_execution_cannot_close_decision_loop(self):
        with self.assertRaises(ValueError):
            DecisionOutcomeEvaluator().evaluate(
                self.decision(), self.execution("VERIFIED"), outcome_positive=True
            )


if __name__ == "__main__":
    unittest.main()
