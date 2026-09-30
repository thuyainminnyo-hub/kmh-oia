import unittest

from src.recovery_controller import RecoveryController


class Stage14RecoveryControllerTests(unittest.TestCase):
    def test_start_requires_valid_operation_and_budget(self):
        controller = RecoveryController()
        with self.assertRaisesRegex(ValueError, "operation"):
            controller.start(operation=" ")
        with self.assertRaisesRegex(ValueError, "positive integer"):
            controller.start(operation="worker", max_attempts=0)

    def test_successful_attempt_recovers(self):
        state = RecoveryController().start(operation="worker", max_attempts=3)
        recovered = RecoveryController().attempt(state, succeeded=True)
        self.assertEqual((1, "recovered"), (recovered.attempts, recovered.phase))

    def test_failed_attempts_are_bounded(self):
        controller = RecoveryController()
        state = controller.start(operation="worker", max_attempts=2)
        retrying = controller.attempt(state, succeeded=False)
        exhausted = controller.attempt(retrying, succeeded=False)
        self.assertEqual((1, "retrying"), (retrying.attempts, retrying.phase))
        self.assertEqual((2, "exhausted"), (exhausted.attempts, exhausted.phase))

    def test_validation_requires_recovery_and_health(self):
        controller = RecoveryController()
        recovered = controller.attempt(controller.start(operation="worker"), succeeded=True)
        with self.assertRaisesRegex(RuntimeError, "health gate failed"):
            controller.validate(recovered, health_passed=False)
        controller.validate(recovered, health_passed=True)


if __name__ == "__main__":
    unittest.main()
