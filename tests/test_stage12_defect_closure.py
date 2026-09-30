import unittest

from src.components import OIARuntime
from src.evaluation import EvaluationResult
from src.memory import InMemoryMemoryStore
from src.state import StateStore


class RejectingEvaluator:
    def evaluate(self, result):
        return EvaluationResult(False, "pv9 validation rejection")


class Stage12DefectClosureValidationTests(unittest.TestCase):
    def test_pv9_no_open_repository_defect_path_for_normal_runtime(self):
        runtime = OIARuntime()
        response, stages, events = runtime.execute_detailed(
            "defect closure validation",
            session_id="pv9-success",
        )

        self.assertEqual(response, "defect closure validation")
        self.assertEqual(events[-1].stage, "trace")
        self.assertEqual(events[-1].status, "ok")
        self.assertEqual(
            stages,
            [
                "input_gateway", "oia_core", "context_assembly", "workflow",
                "agent", "state", "tool_security", "governed_tool",
                "evaluation", "response", "trace",
            ],
        )

    def test_pv9_known_evaluation_failure_is_rolled_back_and_classified(self):
        state = StateStore()
        memory = InMemoryMemoryStore()
        state.set("pv9-failure", "before", "state")
        memory.update("pv9-failure", "before", "memory")
        runtime = OIARuntime(
            state=state,
            memory=memory,
            evaluator=RejectingEvaluator(),
        )

        with self.assertRaises(ValueError):
            runtime.execute_detailed(
                "known validation failure",
                session_id="pv9-failure",
            )

        self.assertEqual(state.snapshot("pv9-failure"), {"before": "state"})
        self.assertEqual(
            [(item.key, item.value) for item in memory.snapshot("pv9-failure")],
            [("before", "memory")],
        )
        self.assertEqual(runtime.tracer.events[-2].stage, "rollback")
        self.assertEqual(runtime.tracer.events[-1].stage, "error")
        self.assertEqual(runtime.tracer.events[-1].metadata["status"], "validation")


if __name__ == "__main__":
    unittest.main()
