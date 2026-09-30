import unittest

from src.main import run


class TestTextPath(unittest.TestCase):
    def test_end_to_end_text_path(self):
        response, trace = run("hello OIA")
        self.assertEqual(response, "hello OIA")
        self.assertEqual(
            trace.stages,
            [
                "input_gateway",
                "oia_core",
                "context_assembly",
                "workflow",
                "agent",
                "state",
                "tool_security",
                "governed_tool",
                "evaluation",
                "response",
                "trace",
            ],
        )
        self.assertEqual(len(trace.events), len(trace.stages))
        self.assertEqual(trace.events[-1].stage, "trace")

    def test_empty_goal_is_rejected(self):
        with self.assertRaises(ValueError):
            run("   ")

    def test_unlisted_tool_is_blocked_before_execution(self):
        with self.assertRaises(PermissionError):
            run("blocked", tool_name="shell")

    def test_blocked_tool_event_contains_security_metadata(self):
        from src.components import OIARuntime
        runtime = OIARuntime()
        with self.assertRaises(PermissionError):
            runtime.execute_detailed("blocked", tool_name="shell")


if __name__ == "__main__":
    unittest.main()
