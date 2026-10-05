import unittest

from src.decision_command_bridge import DecisionCommandBridge
from src.decision_queue import DecisionQueue
from src.live_operating_console import LiveOperatingConsole
from src.telemetry_signal_engine import IntelligenceSignal


class DecisionCommandBridgeTests(unittest.TestCase):
    def signal(self):
        return IntelligenceSignal(
            "QUALITY_RISK", "HIGH", "qa_pass_rate", 0.5, 0.8,
            "QA is low.", "Review failed executions."
        )

    def test_approved_decision_becomes_command(self):
        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        queue.decide(decision.id, approved=True)
        console = LiveOperatingConsole(date="2026-10-05")
        applied = DecisionCommandBridge().apply(
            queue, console, decision.id, expected_output="quality restored"
        )
        command = console.snapshot().commands[0]
        self.assertEqual(applied.decision_id, decision.id)
        self.assertEqual(applied.command_id, command.id)
        self.assertEqual(command.objective, "Review failed executions.")
        self.assertEqual(command.status, "INBOX")

    def test_pending_decision_cannot_execute_as_command(self):
        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        with self.assertRaises(ValueError):
            DecisionCommandBridge().apply(
                queue, LiveOperatingConsole(date="2026-10-05"),
                decision.id, expected_output="quality restored"
            )

    def test_rejected_decision_cannot_execute_as_command(self):
        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        queue.decide(decision.id, approved=False)
        with self.assertRaises(ValueError):
            DecisionCommandBridge().apply(
                queue, LiveOperatingConsole(date="2026-10-05"),
                decision.id, expected_output="quality restored"
            )

    def test_expected_output_is_required(self):
        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        queue.decide(decision.id, approved=True)
        with self.assertRaises(ValueError):
            DecisionCommandBridge().apply(
                queue, LiveOperatingConsole(date="2026-10-05"),
                decision.id, expected_output=""
            )


if __name__ == "__main__":
    unittest.main()
