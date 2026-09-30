import tempfile
import unittest
from pathlib import Path

from src.components import OIARuntime
from src.memory import InMemoryMemoryStore
from src.state import JsonFileStateStore


class RejectingEvaluator:
    def evaluate(self, result):
        from src.evaluation import EvaluationResult
        return EvaluationResult(False, "persistence rollback validation")


class Stage13PersistenceTests(unittest.TestCase):
    def test_json_state_survives_runtime_recreation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            first = JsonFileStateStore(path)
            runtime = OIARuntime(state=first)
            runtime.execute_detailed("persisted goal", session_id="stage13")
            recreated = JsonFileStateStore(path)
            self.assertEqual(recreated.snapshot("stage13")["last_goal"], "persisted goal")

    def test_json_state_rejects_invalid_root_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                JsonFileStateStore(path)

    def test_local_state_and_memory_rollback_remain_consistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = JsonFileStateStore(Path(tmp) / "state.json")
            memory = InMemoryMemoryStore()
            state.set("stage13", "before", "state")
            memory.update("stage13", "before", "memory")
            runtime = OIARuntime(state=state, memory=memory, evaluator=RejectingEvaluator())
            with self.assertRaises(ValueError):
                runtime.execute_detailed("rollback", session_id="stage13")
            self.assertEqual(state.snapshot("stage13"), {"before": "state"})
            self.assertEqual(
                [(entry.key, entry.value) for entry in memory.snapshot("stage13")],
                [("before", "memory")],
            )


if __name__ == "__main__":
    unittest.main()
