import unittest

from src.execution_telemetry import ExecutionTelemetry, ExecutionTelemetryCollector


class ExecutionTelemetryTests(unittest.TestCase):
    def test_empty_snapshot_is_safe(self):
        snapshot = ExecutionTelemetryCollector().snapshot()
        self.assertEqual(snapshot.executions, 0)
        self.assertEqual(snapshot.qa_pass_rate, 0.0)
        self.assertIsNone(snapshot.standard_compliance_rate)

    def test_snapshot_aggregates_operational_health(self):
        collector = ExecutionTelemetryCollector()
        collector.record(ExecutionTelemetry("cmd:1", True, False, False, 4, True, False, False, None))
        collector.record(ExecutionTelemetry("cmd:2", False, True, True, 0, False, True, True, "REVISE"))
        snapshot = collector.snapshot()
        self.assertEqual(snapshot.executions, 2)
        self.assertEqual(snapshot.qa_pass_rate, 0.5)
        self.assertEqual(snapshot.blocked_rate, 0.5)
        self.assertEqual(snapshot.rework_rate, 0.5)
        self.assertEqual(snapshot.evidence_coverage, 0.5)
        self.assertEqual(snapshot.standard_compliance_rate, 0.5)
        self.assertEqual(snapshot.drift_rate, 0.5)
        self.assertEqual(snapshot.revalidation_rate, 0.5)
        self.assertEqual(snapshot.learning_rate, 0.5)

    def test_negative_evidence_count_is_rejected(self):
        with self.assertRaises(ValueError):
            ExecutionTelemetryCollector().record(
                ExecutionTelemetry("cmd:1", True, False, False, -1, None, False, False, None)
            )


if __name__ == "__main__":
    unittest.main()
