import unittest

from src.components import OIARuntime
from src.evaluation import EvaluationResult
from src.memory import InMemoryMemoryStore


class RejectingEvaluator:
    def evaluate(self, result):
        return EvaluationResult(False, "rejected for rollback test")


class RollbackTests(unittest.TestCase):
    def test_failed_execution_restores_state_and_memory(self):
        memory = InMemoryMemoryStore()
        memory.update("session-a", "last_goal", "before")
        memory.update("session-a", "custom", "keep")

        runtime = OIARuntime(memory=memory, evaluator=RejectingEvaluator())
        runtime.state.set("session-a", "last_goal", "before")

        with self.assertRaises(ValueError):
            runtime.execute_detailed("after", session_id="session-a")

        self.assertEqual(
            {item.key: item.value for item in memory.retrieve("session-a")},
            {"last_goal": "before", "custom": "keep"},
        )
        self.assertEqual(runtime.state.get("session-a").values, {"last_goal": "before"})
        self.assertEqual(runtime.tracer.events[-2].stage, "rollback")
        self.assertEqual(runtime.tracer.events[-2].status, "ok")
        self.assertEqual(runtime.tracer.events[-1].stage, "error")


if __name__ == "__main__":
    unittest.main()
