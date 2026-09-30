import unittest

from src.rollback import RollbackController


class Stage14RollbackTests(unittest.TestCase):
    def test_prepare_requires_distinct_releases(self):
        controller = RollbackController()
        with self.assertRaisesRegex(ValueError, "differ"):
            controller.prepare(release_id="r1", previous_release_id="r1")

    def test_execute_preserves_trigger_and_evidence(self):
        controller = RollbackController()
        state = controller.prepare(release_id="r2", previous_release_id="r1")
        rolled = controller.execute(state, trigger="health gate failed")
        self.assertEqual("rolled_back", rolled.phase)
        self.assertEqual("health gate failed", rolled.reason)
        self.assertTrue(rolled.evidence_preserved)

    def test_execute_requires_trigger(self):
        controller = RollbackController()
        state = controller.prepare(release_id="r2", previous_release_id="r1")
        with self.assertRaisesRegex(ValueError, "trigger"):
            controller.execute(state, trigger=" ")

    def test_validation_requires_previous_release_and_health(self):
        controller = RollbackController()
        state = controller.execute(
            controller.prepare(release_id="r2", previous_release_id="r1"),
            trigger="error threshold exceeded",
        )
        with self.assertRaisesRegex(RuntimeError, "previous release unavailable"):
            controller.validate(state, previous_release_available=False, health_passed=True)
        with self.assertRaisesRegex(RuntimeError, "health gate failed"):
            controller.validate(state, previous_release_available=True, health_passed=False)
        controller.validate(state, previous_release_available=True, health_passed=True)


if __name__ == "__main__":
    unittest.main()
