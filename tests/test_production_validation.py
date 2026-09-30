import unittest

from src.agent import AgentDecision
from src.components import OIARuntime
from src.evaluation import EvaluationResult
from src.memory import InMemoryMemoryStore
from src.security import ToolSecurityPolicy
from src.state import StateStore


class FixedAgent:
    def decide(self, request):
        return AgentDecision("echo", request.goal, "functional-validation")


class RejectingEvaluator:
    def evaluate(self, result):
        return EvaluationResult(False, "functional validation rejection")


class ProductionFunctionalValidationTests(unittest.TestCase):
    def test_pv1_happy_path_covers_required_runtime_functions(self):
        memory = InMemoryMemoryStore()
        state = StateStore()
        runtime = OIARuntime(
            state=state,
            memory=memory,
            agent=FixedAgent(),
        )

        response, stages, events = runtime.execute_detailed(
            "functional validation goal",
            session_id="pv1",
        )

        self.assertEqual(response, "functional validation goal")
        self.assertEqual(
            stages,
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
        self.assertEqual(state.get("pv1").values["last_goal"], "functional validation goal")
        stored = {item.key: item.value for item in memory.retrieve("pv1")}
        self.assertEqual(stored["last_goal"], "functional validation goal")
        self.assertEqual(stored["last_response"], response)
        self.assertEqual(events[-1].stage, "trace")

    def test_pv1_input_validation_rejects_empty_goal(self):
        with self.assertRaises(ValueError):
            OIARuntime().execute("   ")

    def test_pv1_authorization_denial_stops_tool_execution(self):
        runtime = OIARuntime(
            security=ToolSecurityPolicy(allowed_tools={"other-tool"}),
        )
        with self.assertRaises(PermissionError):
            runtime.execute("blocked tool", session_id="pv1-auth", tool_name="echo")

        self.assertEqual(
            runtime.tracer.events[-1].stage,
            "error",
        )
        self.assertEqual(
            runtime.tracer.events[-1].metadata["status"],
            "authorization",
        )

    def test_pv1_evaluation_rejection_uses_recovery_boundary(self):
        memory = InMemoryMemoryStore()
        memory.update("pv1-eval", "existing", "keep")
        runtime = OIARuntime(
            memory=memory,
            evaluator=RejectingEvaluator(),
        )

        with self.assertRaises(ValueError):
            runtime.execute("evaluation rejection", session_id="pv1-eval")

        stored = {item.key: item.value for item in memory.retrieve("pv1-eval")}
        self.assertEqual(stored, {"existing": "keep"})
        self.assertEqual(runtime.tracer.events[-2].stage, "rollback")
        self.assertEqual(runtime.tracer.events[-1].stage, "error")


if __name__ == "__main__":
    unittest.main()
