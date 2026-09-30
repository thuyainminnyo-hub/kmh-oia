import unittest

from src.agent import AgentDecision
from src.components import OIARuntime
from src.evaluation import EvaluationResult
from src.memory import InMemoryMemoryStore
from src.recovery import (
    DeterministicRecoveryPolicy,
    RecoveryConfig,
    RetryableExecutionError,
)
from src.tools import ToolRequest, ToolResult


class FlakyExecutor:
    def __init__(self, failures=2):
        self.failures = failures
        self.attempts = 0

    def execute(self, request: ToolRequest) -> ToolResult:
        self.attempts += 1
        if self.attempts <= self.failures:
            raise RetryableExecutionError("temporary dependency failure")
        return ToolResult(request.tool_name, "recovered", True, "temporary dependency recovered")


class FixedAgent:
    def decide(self, request):
        return AgentDecision("echo", request.goal, "pv5")


class RejectingEvaluator:
    def evaluate(self, result):
        return EvaluationResult(False, "pv5 rollback")


class Stage12ReliabilityTests(unittest.TestCase):
    def test_pv5_repeated_success_preserves_runtime_contract(self):
        runtime = OIARuntime()
        for index in range(10):
            response, stages, events = runtime.execute_detailed(
                f"reliability goal {index}", session_id=f"pv5-{index}"
            )
            self.assertEqual(response, f"reliability goal {index}")
            self.assertEqual(stages[-1], "trace")
            self.assertEqual(events[-1].status, "ok")

        self.assertEqual(len(runtime.tracer.events), 110)

    def test_pv5_dependency_failure_recovers_with_bounded_retry(self):
        executor = FlakyExecutor(failures=2)
        recovery = DeterministicRecoveryPolicy(RecoveryConfig(max_attempts=3))
        runtime = OIARuntime(
            registry=executor,
            recovery=recovery,
            agent=FixedAgent(),
        )

        response, stages, events = runtime.execute_detailed(
            "dependency recovery", session_id="pv5-retry"
        )

        self.assertEqual(response, "recovered")
        self.assertEqual(executor.attempts, 3)
        self.assertEqual(stages[-1], "trace")
        self.assertEqual(events[-1].status, "ok")

    def test_pv5_cancellation_stops_execution_before_dependency_call(self):
        executor = FlakyExecutor()
        recovery = DeterministicRecoveryPolicy(
            RecoveryConfig(max_attempts=3, is_cancelled=lambda: True)
        )
        runtime = OIARuntime(
            registry=executor,
            recovery=recovery,
            agent=FixedAgent(),
        )

        with self.assertRaises(Exception) as raised:
            runtime.execute_detailed("cancelled dependency", session_id="pv5-cancel")

        self.assertEqual(raised.exception.__class__.__name__, "CancelledError")
        self.assertEqual(executor.attempts, 0)
        self.assertEqual(runtime.tracer.events[-2].stage, "rollback")
        self.assertEqual(runtime.tracer.events[-1].status, "recovery")

    def test_pv5_failure_restores_state_and_memory(self):
        memory = InMemoryMemoryStore()
        memory.update("pv5-rollback", "last_goal", "before")
        memory.update("pv5-rollback", "keep", "yes")

        runtime = OIARuntime(
            memory=memory,
            evaluator=RejectingEvaluator(),
        )
        runtime.state.set("pv5-rollback", "last_goal", "before")

        with self.assertRaises(ValueError):
            runtime.execute_detailed("after", session_id="pv5-rollback")

        self.assertEqual(
            {item.key: item.value for item in memory.retrieve("pv5-rollback")},
            {"last_goal": "before", "keep": "yes"},
        )
        self.assertEqual(
            runtime.state.get("pv5-rollback").values,
            {"last_goal": "before"},
        )
        self.assertEqual(runtime.tracer.events[-2].stage, "rollback")
        self.assertEqual(runtime.tracer.events[-2].status, "ok")


if __name__ == "__main__":
    unittest.main()
