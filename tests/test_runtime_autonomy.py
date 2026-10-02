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

    def test_allowed_autonomy_action_and_scope_reaches_tool_execution(self):
        executor = RecordingExecutor()
        policy = AutonomyPolicy({"echo"}, {"staging"})
        runtime = OIARuntime(registry=executor, autonomy_policy=policy, autonomy_scope="staging")

        response, _, events = runtime.execute_detailed("hello", session_id="s1")

        self.assertEqual(response, "hello")
        self.assertEqual(len(executor.calls), 1)
        decision = next(event for event in events if event.stage == "autonomy_policy")
        self.assertEqual(decision.status, "ok")


if __name__ == "__main__": unittest.main()
