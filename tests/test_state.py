import unittest

from src.main import run
from src.state import StateStore


class StateCompatibilityTests(unittest.TestCase):
    def test_state_persists_within_session(self):
        store = StateStore()

        run("first goal", session_id="session-a", state=store)
        response, _ = run("second goal", session_id="session-a", state=store)

        self.assertEqual(response, "second goal")
        self.assertEqual(store.get("session-a").values["last_goal"], "second goal")

    def test_sessions_are_isolated(self):
        store = StateStore()

        run("goal A", session_id="session-a", state=store)
        run("goal B", session_id="session-b", state=store)

        self.assertEqual(store.get("session-a").values["last_goal"], "goal A")
        self.assertEqual(store.get("session-b").values["last_goal"], "goal B")

    def test_state_stage_is_traced(self):
        _, trace = run("trace state", session_id="session-a", state=StateStore())

        self.assertIn("state", trace.stages)


if __name__ == "__main__":
    unittest.main()
