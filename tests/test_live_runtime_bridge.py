import unittest

from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.standardization_engine import OperatingStandard


class LiveRuntimeBridgeTests(unittest.TestCase):
    def test_command_runs_through_runtime_and_becomes_learned(self) -> None:
        console = LiveOperatingConsole(
            date="2026-10-05",
            primary_objective="Execute today's highest-leverage command",
        )
        command = console.add_command(
            objective="hello operating intelligence",
            priority="P1",
            owner="Human + AI",
            expected_output="runtime response",
        )

        record = LiveRuntimeBridge(console).execute(command.id)

        self.assertEqual(record.final_status, "LEARNED")
        self.assertEqual(record.qa_status, "PASS")
        self.assertIn("input_gateway", record.trace_stages)
        self.assertIn("evaluation", record.trace_stages)
        self.assertTrue(any(item.startswith("trace_id=") for item in record.evidence))

    def test_governed_execution_feeds_evidence_back_to_control_plane(self) -> None:
        console = LiveOperatingConsole(date="2026-10-05", primary_objective="Governed execution")
        command = console.add_command(
            objective="execute governed work",
            priority="P1",
            owner="system",
            expected_output="runtime response",
        )
        standard = OperatingStandard(
            "std:a:v1", "a", "Require evidence", "Higher quality", 1, "ACTIVE"
        )

        record = LiveRuntimeBridge(console).execute(
            command.id, standard=standard, applied_rule="Require evidence"
        )

        self.assertIsNotNone(record.standard_feedback)
        self.assertFalse(record.standard_feedback.drift.drifted)
        self.assertIsNone(record.standard_feedback.trigger)

    def test_unknown_command_is_rejected(self) -> None:
        console = LiveOperatingConsole(date="2026-10-05")
        bridge = LiveRuntimeBridge(console)

        with self.assertRaises(KeyError):
            bridge.execute("missing-command")


if __name__ == "__main__":
    unittest.main()
