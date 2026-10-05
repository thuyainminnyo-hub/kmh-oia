import unittest

from src.decision_queue import DecisionQueue
from src.telemetry_signal_engine import IntelligenceSignal


class DecisionQueueTests(unittest.TestCase):
    def signal(self):
        return IntelligenceSignal(
            "QUALITY_RISK", "HIGH", "qa_pass_rate", 0.5, 0.8,
            "QA is low.", "Review failed executions."
        )

    def test_signal_becomes_pending_decision(self):
        queue = DecisionQueue()
        item = queue.enqueue(self.signal(), owner="system")
        self.assertEqual(item.status, "PENDING")
        self.assertEqual(len(queue.pending()), 1)

    def test_decision_can_be_approved_or_rejected(self):
        queue = DecisionQueue()
        approved = queue.enqueue(self.signal(), owner="system")
        self.assertEqual(queue.decide(approved.id, approved=True).status, "APPROVED")

        rejected = queue.enqueue(self.signal(), owner="human")
        self.assertEqual(queue.decide(rejected.id, approved=False).status, "REJECTED")

    def test_owner_is_required(self):
        with self.assertRaises(ValueError):
            DecisionQueue().enqueue(self.signal(), owner="")

    def test_unknown_decision_is_rejected(self):
        with self.assertRaises(KeyError):
            DecisionQueue().decide("missing", approved=True)


if __name__ == "__main__":
    unittest.main()
