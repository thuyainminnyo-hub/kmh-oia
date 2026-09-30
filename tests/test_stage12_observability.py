import unittest

from src.components import OIARuntime
from src.evaluation import EvaluationResult


class RejectingEvaluator:
    def evaluate(self, result):
        return EvaluationResult(False, "pv8 rejection")


class Stage12ObservabilityValidationTests(unittest.TestCase):
    def test_pv8_success_trace_is_ordered_complete_and_context_consistent(self):
        runtime = OIARuntime()
        response, stages, events = runtime.execute_detailed(
            "observability validation",
            session_id="pv8-success",
        )

        self.assertEqual(response, "observability validation")
        self.assertEqual(stages, [
            "input_gateway", "oia_core", "context_assembly", "workflow",
            "agent", "state", "tool_security", "governed_tool",
            "evaluation", "response", "trace",
        ])
        self.assertEqual([event.stage for event in events], stages)
        self.assertEqual(events[-1].status, "ok")
        self.assertEqual(events[-1].metadata["event_count"], str(len(events)))

        keys = (
            "request_id", "session_id", "workflow_id",
            "task_id", "agent_id", "trace_id",
        )
        first = {key: events[0].metadata[key] for key in keys}
        for event in events:
            self.assertEqual(
                {key: event.metadata[key] for key in keys},
                first,
            )
        self.assertEqual(first["session_id"], "pv8-success")

    def test_pv8_failure_trace_records_rollback_and_classified_error(self):
        runtime = OIARuntime(evaluator=RejectingEvaluator())

        with self.assertRaises(ValueError):
            runtime.execute_detailed(
                "observability failure validation",
                session_id="pv8-failure",
            )

        events = runtime.tracer.events
        self.assertEqual(events[-2].stage, "rollback")
        self.assertEqual(events[-2].status, "ok")
        self.assertEqual(events[-1].stage, "error")
        self.assertEqual(events[-1].metadata["status"], "validation")

        keys = (
            "request_id", "session_id", "workflow_id",
            "task_id", "agent_id", "trace_id",
        )
        first = {key: events[0].metadata[key] for key in keys}
        for event in events:
            self.assertEqual(
                {key: event.metadata[key] for key in keys},
                first,
            )
        self.assertEqual(first["session_id"], "pv8-failure")


if __name__ == "__main__":
    unittest.main()
