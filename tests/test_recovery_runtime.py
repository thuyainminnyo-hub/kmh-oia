import unittest

from src.agent import AgentDecision
from src.components import OIARuntime
from src.recovery import DeterministicRecoveryPolicy, RecoveryConfig, RetryableExecutionError
from src.tools import ToolRequest, ToolResult


class FlakyExecutor:
    def __init__(self):
        self.attempts = 0

    def execute(self, request: ToolRequest) -> ToolResult:
        self.attempts += 1
        if self.attempts < 2:
            raise RetryableExecutionError("temporary tool failure")
        return ToolResult(request.tool_name, request.input_text, True, "recovered")


class CancelledExecutor:
    def execute(self, request: ToolRequest) -> ToolResult:
        return ToolResult(request.tool_name, request.input_text, True, "unused")


class FixedAgent:
    def decide(self, request: object) -> AgentDecision:
        return AgentDecision("echo", "recovered", "recovery test")


class RecoveryRuntimeTests(unittest.TestCase):
    def test_runtime_retries_tool_execution_with_bounded_policy(self):
        executor = FlakyExecutor()
        recovery = DeterministicRecoveryPolicy(RecoveryConfig(max_attempts=2))
        runtime = OIARuntime(registry=executor, recovery=recovery, agent=FixedAgent())
        response, _, _ = runtime.execute_detailed("goal")
        self.assertEqual(response, "recovered")
        self.assertEqual(executor.attempts, 2)

    def test_runtime_propagates_cancellation_as_recovery_error(self):
        recovery = DeterministicRecoveryPolicy(
            RecoveryConfig(max_attempts=2, is_cancelled=lambda: True)
        )
        runtime = OIARuntime(registry=CancelledExecutor(), recovery=recovery)
        with self.assertRaises(Exception) as raised:
            runtime.execute_detailed("cancelled")
        self.assertEqual(raised.exception.__class__.__name__, "CancelledError")
        self.assertEqual(runtime.tracer.events[-1].stage, "error")
        self.assertEqual(runtime.tracer.events[-1].status, "recovery")


if __name__ == "__main__":
    unittest.main()
