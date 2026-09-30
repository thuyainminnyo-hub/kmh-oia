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

    def test_empty_goal_is_rejected(self):
        with self.assertRaises(ValueError):
            run("   ")

    def test_unlisted_tool_is_blocked_before_execution(self):
        with self.assertRaises(PermissionError):
            run("blocked", tool_name="shell")


if __name__ == "__main__":
    unittest.main()
