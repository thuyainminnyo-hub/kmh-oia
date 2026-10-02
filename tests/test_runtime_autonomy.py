import unittest

from src.autonomy_policy import AutonomyPolicy
from src.components import OIARuntime
from src.tools import ToolExecutor, ToolRequest, ToolResult


class RecordingExecutor(ToolExecutor):
    def __init__(self):
        self.calls = []

    def execute(self, request: ToolRequest) -> ToolResult:
        self.calls.append(request)
        return ToolResult(request.tool_name, request.input_text, True, "recorded")


class RuntimeAutonomyEnforcementTests(unittest.TestCase):
    def test_denied_autonomy_scope_blocks_before_tool_execution(self):
        executor = RecordingExecutor()
        policy = AutonomyPolicy({"echo"}, {"staging"})
        runtime = OIARuntime(registry=executor, autonomy_policy=policy, autonomy_scope="production")

        with self.assertRaises(PermissionError):
            runtime.execute_detailed("hello", session_id="s1")

        self.assertEqual(executor.calls, [])
        event = next(event for event in runtime.tracer.events if event.stage == "tool_security")
        self.assertEqual(event.status, "blocked")
        self.assertEqual(event.metadata["autonomy_status"], "blocked")
        self.assertEqual(event.metadata["autonomy_scope"], "production")

    def test_allowed_autonomy_action_and_scope_reaches_tool_execution(self):
        executor = RecordingExecutor()
        policy = AutonomyPolicy({"echo"}, {"staging"})
        runtime = OIARuntime(registry=executor, autonomy_policy=policy, autonomy_scope="staging")

        response, _, events = runtime.execute_detailed("hello", session_id="s1")

        self.assertEqual(response, "hello")
        self.assertEqual(len(executor.calls), 1)
        event = next(event for event in events if event.stage == "tool_security")
        self.assertEqual(event.status, "ok")
        self.assertEqual(event.metadata["autonomy_status"], "ok")
        self.assertEqual(event.metadata["autonomy_scope"], "staging")


if __name__ == "__main__":
    unittest.main()
