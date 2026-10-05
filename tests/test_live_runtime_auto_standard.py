import unittest

from src.active_standard_resolver import ActiveStandardResolver
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.standardization_engine import OperatingStandard


class LiveRuntimeAutoStandardTests(unittest.TestCase):
    def test_command_auto_resolves_active_standard_and_executes(self):
        console = LiveOperatingConsole("2026-10-05", "Governed execution")
        command = console.add_command(
            "cmd:auto",
            objective="execute governed task",
            priority="P1",
            owner="system",
            expected_output="successful execution",
            next_action="review result",
        )
        resolver = ActiveStandardResolver()
        resolver.register(
            OperatingStandard(
                "std:auto:v1",
                "auto",
                "Require evidence",
                "Trace-backed execution",
                1,
                "ACTIVE",
            )
        )
        record = LiveRuntimeBridge(
            console,
            standard_resolver=resolver,
        ).execute(
            command.id,
            source_adaptation_id="auto",
            applied_rule="Require evidence",
        )
        self.assertEqual(record.standard_id, "std:auto:v1")
        self.assertEqual(record.qa_status, "PASS")
        self.assertEqual(record.final_status, "LEARNED")
        self.assertIsNotNone(record.standard_feedback)

    def test_missing_active_standard_blocks_before_command_transition(self):
        console = LiveOperatingConsole("2026-10-05", "Governed execution")
        command = console.add_command(
            "cmd:missing",
            objective="execute governed task",
            priority="P1",
            owner="system",
            expected_output="successful execution",
        )
        with self.assertRaises(LookupError):
            LiveRuntimeBridge(console).execute(
                command.id,
                source_adaptation_id="missing",
                applied_rule="Anything",
            )
        self.assertEqual(command.status, "INBOX")

    def test_wrong_rule_blocks_before_command_transition(self):
        console = LiveOperatingConsole("2026-10-05", "Governed execution")
        command = console.add_command(
            "cmd:wrong",
            objective="execute governed task",
            priority="P1",
            owner="system",
            expected_output="successful execution",
        )
        resolver = ActiveStandardResolver()
        resolver.register(
            OperatingStandard(
                "std:auto:v1",
                "auto",
                "Require evidence",
                "Trace-backed execution",
                1,
                "ACTIVE",
            )
        )
        with self.assertRaises(PermissionError):
            LiveRuntimeBridge(
                console,
                standard_resolver=resolver,
            ).execute(
                command.id,
                source_adaptation_id="auto",
                applied_rule="Skip evidence",
            )
        self.assertEqual(command.status, "INBOX")


if __name__ == "__main__":
    unittest.main()
