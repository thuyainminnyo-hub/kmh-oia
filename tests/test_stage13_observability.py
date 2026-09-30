import unittest

from src.trace import InMemoryTracer, TraceEvent


class Stage13ObservabilityTests(unittest.TestCase):
    def _event(self, stage="test", status="ok", trace_id="t1"):
        context = {
            "request_id": "r1", "session_id": "s1",
            "workflow_id": "w1", "task_id": "k1",
            "agent_id": "a1", "trace_id": trace_id,
        }
        return TraceEvent(stage, status, context)

    def test_emit_requires_stage_status_and_context(self):
        tracer = InMemoryTracer()
        with self.assertRaises(ValueError):
            tracer.emit(self._event(stage=""))
        with self.assertRaises(ValueError):
            tracer.emit(self._event(status=""))
        missing = TraceEvent("test", "ok", {"trace_id": "t1"})
        with self.assertRaises(ValueError):
            tracer.emit(missing)

    def test_validate_integrity_accepts_consistent_completed_trace(self):
        tracer = InMemoryTracer()
        tracer.emit(self._event("input_gateway"))
        tracer.emit(self._event("trace"))
        tracer.validate_integrity()

    def test_validate_integrity_rejects_context_drift(self):
        tracer = InMemoryTracer()
        tracer.emit(self._event("input_gateway"))
        tracer.emit(self._event("trace", trace_id="different"))
        with self.assertRaises(ValueError):
            tracer.validate_integrity()

    def test_validate_integrity_rejects_empty_trace(self):
        with self.assertRaises(ValueError):
            InMemoryTracer().validate_integrity()


if __name__ == "__main__":
    unittest.main()
