import unittest

from src.execution_telemetry import SystemHealthSnapshot
from src.telemetry_signal_engine import TelemetrySignalEngine


class TelemetrySignalEngineTests(unittest.TestCase):
    def test_healthy_snapshot_has_no_signals(self):
        snapshot = SystemHealthSnapshot(10, 0.95, 0.05, 0.05, 1.0, 1.0, 0.0, 0.0, 0.95)
        self.assertEqual(TelemetrySignalEngine().analyze(snapshot), [])

    def test_unhealthy_snapshot_emits_actionable_signals(self):
        snapshot = SystemHealthSnapshot(10, 0.60, 0.40, 0.30, 0.50, 0.80, 0.25, 0.20, 0.50)
        signals = TelemetrySignalEngine().analyze(snapshot)
        kinds = {signal.kind for signal in signals}
        self.assertEqual(
            kinds,
            {"QUALITY_RISK", "FLOW_RISK", "REWORK_RISK", "EVIDENCE_GAP", "STANDARD_DRIFT"},
        )
        self.assertTrue(all(signal.recommended_action.strip() for signal in signals))

    def test_zero_execution_snapshot_is_not_a_failure(self):
        snapshot = SystemHealthSnapshot(0, 0.0, 0.0, 0.0, 0.0, None, 0.0, 0.0, 0.0)
        self.assertEqual(TelemetrySignalEngine().analyze(snapshot), [])

    def test_invalid_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            TelemetrySignalEngine(min_qa_pass_rate=1.2)


if __name__ == "__main__":
    unittest.main()
