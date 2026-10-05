import unittest

from src.active_standard_resolver import ActiveStandardResolver
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.standard_control_plane import StandardControlPlane
from src.standardization_engine import OperatingStandard


class LiveRuntimeRevalidationIntegrationTests(unittest.TestCase):
    def test_governed_execution_completes_with_standard_feedback(self):
        console = LiveOperatingConsole("2026-10-05", "Governed execution")
        command = console.add_command(
            "cmd:e2e",
            objective="execute governed task",
            priority="P1",
            owner="system",
            expected_output="successful execution",
        )
        control_plane = StandardControlPlane()
        resolver = ActiveStandardResolver(control_plane.registry)
        standard = OperatingStandard(
            "std:e2e:v1",
            "e2e",
            "Require evidence",
            "Trace-backed execution",
            1,
            "ACTIVE",
        )
        resolver.register(standard)

        record = LiveRuntimeBridge(
            console,
            control_plane=control_plane,
            standard_resolver=resolver,
        ).execute(
            command.id,
            source_adaptation_id="e2e",
            applied_rule="Require evidence",
            observed_effect=1.0,
            outcome_positive=True,
        )

        self.assertEqual(record.standard_id, "std:e2e:v1")
        self.assertEqual(record.qa_status, "PASS")
        self.assertEqual(record.final_status, "LEARNED")
        self.assertIsNotNone(record.standard_feedback)
        self.assertIsNotNone(record.revalidation)
        self.assertFalse(record.revalidation.revalidated)
        self.assertIsNone(record.revalidation.control_result.trigger)

    def test_governance_failure_blocks_before_runtime(self):
        console = LiveOperatingConsole("2026-10-05", "Governed execution")
        command = console.add_command(
            "cmd:block",
            objective="execute governed task",
            priority="P1",
            owner="system",
            expected_output="successful execution",
        )
        control_plane = StandardControlPlane()
        resolver = ActiveStandardResolver(control_plane.registry)
        resolver.register(
            OperatingStandard(
                "std:e2e:v1",
                "e2e",
                "Require evidence",
                "Trace-backed execution",
                1,
                "ACTIVE",
            )
        )

        with self.assertRaises(PermissionError):
            LiveRuntimeBridge(
                console,
                control_plane=control_plane,
                standard_resolver=resolver,
            ).execute(
                command.id,
                source_adaptation_id="e2e",
                applied_rule="Skip evidence",
            )

        self.assertEqual(command.status, "INBOX")


if __name__ == "__main__":
    unittest.main()
