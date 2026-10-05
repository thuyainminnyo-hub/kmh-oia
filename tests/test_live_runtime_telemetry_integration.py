import unittest

from src.execution_telemetry import ExecutionTelemetryCollector
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge


class LiveRuntimeTelemetryIntegrationTests(unittest.TestCase):
    def test_execution_auto_captures_health_telemetry(self):
        console = LiveOperatingConsole(
            date="2026-10-05",
            primary_objective="Telemetry integration",
        )
        command = console.add_command(
            objective="execute telemetry task",
            priority="P1",
            owner="system",
            expected_output="runtime response",
        )
        collector = ExecutionTelemetryCollector()
        record = LiveRuntimeBridge(
            console,
            telemetry_collector=collector,
        ).execute(command.id)

        self.assertIsNotNone(record.telemetry)
        self.assertEqual(record.telemetry.command_id, command.id)
        self.assertTrue(record.telemetry.qa_passed)
        self.assertGreater(record.telemetry.evidence_count, 0)
        self.assertEqual(collector.snapshot().executions, 1)
        self.assertEqual(collector.snapshot().qa_pass_rate, 1.0)
        self.assertEqual(collector.snapshot().evidence_coverage, 1.0)

    def test_governed_execution_records_standard_compliance(self):
        console = LiveOperatingConsole(
            date="2026-10-05",
            primary_objective="Governed telemetry",
        )
        command = console.add_command(
            objective="execute governed telemetry task",
            priority="P1",
            owner="system",
            expected_output="runtime response",
        )
        from src.standard_control_plane import StandardControlPlane
        from src.active_standard_resolver import ActiveStandardResolver
        from src.standardization_engine import OperatingStandard

        control_plane = StandardControlPlane()
        resolver = ActiveStandardResolver(control_plane.registry)
        standard = OperatingStandard(
            "std:telemetry:v1",
            "telemetry",
            "Require evidence",
            "Trace-backed execution",
            1,
            "ACTIVE",
        )
        resolver.register(standard)
        collector = ExecutionTelemetryCollector()

        record = LiveRuntimeBridge(
            console,
            control_plane=control_plane,
            standard_resolver=resolver,
            telemetry_collector=collector,
        ).execute(
            command.id,
            source_adaptation_id="telemetry",
            applied_rule="Require evidence",
        )

        self.assertTrue(record.telemetry.standard_compliant)
        self.assertFalse(record.telemetry.drift_detected)
        self.assertEqual(collector.snapshot().standard_compliance_rate, 1.0)


if __name__ == "__main__":
    unittest.main()
