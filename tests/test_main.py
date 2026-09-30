import unittest

from src.main import run
from src.trace import InMemoryTracer


class TestTextPath(unittest.TestCase):
    def test_end_to_end_text_path(self):
        response, trace = run("hello OIA")
        self.assertEqual(response, "hello OIA")
        self.assertEqual(trace.stages, ["input_gateway", "oia_core", "context_assembly", "workflow", "agent", "state", "tool_security", "governed_tool", "evaluation", "response", "trace"])
        self.assertEqual(len(trace.events), len(trace.stages))
        self.assertEqual(trace.events[-1].stage, "trace")

    def test_empty_goal_is_rejected(self):
        with self.assertRaises(ValueError): run("   ")

    def test_unlisted_tool_is_blocked_before_execution(self):
        with self.assertRaises(PermissionError): run("blocked", tool_name="shell")

    def test_blocked_tool_event_contains_security_metadata(self):
        from src.components import OIARuntime
        runtime = OIARuntime()
        with self.assertRaises(PermissionError): runtime.execute_detailed("blocked", tool_name="shell")

    def test_custom_tracer_receives_ordered_events(self):
        from src.components import OIARuntime
        tracer = InMemoryTracer()
        response, stages, events = OIARuntime(tracer=tracer).execute_detailed("hello")
        self.assertEqual(response, "hello")
        self.assertEqual(events, tracer.events)
        self.assertEqual([event.stage for event in tracer.events], stages)
        self.assertEqual(tracer.events[0].stage, "input_gateway")
        self.assertEqual(tracer.events[-1].stage, "trace")

if __name__ == "__main__": unittest.main()
