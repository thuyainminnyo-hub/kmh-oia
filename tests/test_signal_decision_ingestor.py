import unittest

from src.decision_queue import DecisionQueue
from src.signal_decision_ingestor import SignalDecisionIngestor
from src.telemetry_signal_engine import IntelligenceSignal


class SignalDecisionIngestorTests(unittest.TestCase):
    def signal(self, kind="QUALITY_RISK"):
        return IntelligenceSignal(
            kind, "HIGH", "qa_pass_rate", 0.5, 0.8,
            "QA is low.", "Review failed executions."
        )

    def test_signals_are_automatically_ingested_as_pending(self):
        queue = DecisionQueue()
        result = SignalDecisionIngestor(queue).ingest(
            [self.signal(), self.signal("FLOW_RISK")], owner="system"
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(len(queue.pending()), 2)
        self.assertTrue(all(item.status == "PENDING" for item in queue.pending()))

    def test_ingest_never_approves_a_signal(self):
        queue = DecisionQueue()
        SignalDecisionIngestor(queue).ingest_one(self.signal(), owner="system")
        self.assertEqual(queue.pending()[0].status, "PENDING")

    def test_owner_is_required(self):
        with self.assertRaises(ValueError):
            SignalDecisionIngestor().ingest([self.signal()], owner="")

    def test_empty_signal_list_is_safe(self):
        queue = DecisionQueue()
        self.assertEqual(SignalDecisionIngestor(queue).ingest([], owner="system"), [])
        self.assertEqual(queue.pending(), [])


if __name__ == "__main__":
    unittest.main()
