import unittest

from src.production_readiness import TelemetryActivationController
from src.trace import TraceEvent


class Stage14TelemetryTests(unittest.TestCase):
    def _event(self, status="ok"):
        return TraceEvent("response", status, {
            "request_id": "r1", "session_id": "s1", "workflow_id": "w1",
            "task_id": "t1", "agent_id": "a1", "trace_id": "x1",
        })

    def test_activation_requires_events(self):
        with self.assertRaisesRegex(ValueError, "trace events"):
            TelemetryActivationController().activate([])

    def test_activation_marks_valid_trace_evidence_ready(self):
        state = TelemetryActivationController().activate([self._event()])
        self.assertEqual((True, True, True, True), (
            state.trace_active, state.required_context_present,
            state.integrity_validated, state.evidence_ready,
        ))

    def test_activation_blocks_missing_context(self):
        event = self._event()
        event = TraceEvent(event.stage, event.status, {"request_id": "r1"})
        state = TelemetryActivationController().activate([event])
        self.assertFalse(state.required_context_present)
        self.assertFalse(state.integrity_validated)
        self.assertFalse(state.evidence_ready)

    def test_activation_rejects_invalid_terminal_status(self):
        state = TelemetryActivationController().activate([self._event("running")])
        self.assertTrue(state.required_context_present)
        self.assertFalse(state.integrity_validated)
        self.assertFalse(state.evidence_ready)


if __name__ == "__main__":
    unittest.main()
