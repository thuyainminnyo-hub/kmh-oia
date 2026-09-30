import unittest
import time

from src.recovery import (
    CancelledError,
    DeterministicRecoveryPolicy,
    RecoveryConfig,
    RetryableExecutionError,
)


class RecoveryPolicyTests(unittest.TestCase):
    def test_retry_is_bounded_and_succeeds(self):
        attempts = []
        def operation():
            attempts.append(1)
            if len(attempts) < 3:
                raise RetryableExecutionError("temporary")
            return "ok"

        result = DeterministicRecoveryPolicy(RecoveryConfig(max_attempts=3)).run(operation)
        self.assertEqual(result, "ok")
        self.assertEqual(len(attempts), 3)

    def test_retry_budget_exhaustion_is_propagated(self):
        attempts = []
        def operation():
            attempts.append(1)
            raise RetryableExecutionError("still failing")

        with self.assertRaises(RetryableExecutionError):
            DeterministicRecoveryPolicy(RecoveryConfig(max_attempts=2)).run(operation)
        self.assertEqual(len(attempts), 2)

    def test_cancellation_is_checked_before_execution(self):
        with self.assertRaises(CancelledError):
            DeterministicRecoveryPolicy(
                RecoveryConfig(max_attempts=3, is_cancelled=lambda: True)
            ).run(lambda: "never")

    def test_timeout_is_checked_after_operation(self):
        with self.assertRaises(TimeoutError):
            DeterministicRecoveryPolicy(
                RecoveryConfig(timeout_seconds=0.001)
            ).run(lambda: time.sleep(0.01))

    def test_invalid_retry_budget_is_rejected(self):
        with self.assertRaises(ValueError):
            DeterministicRecoveryPolicy(RecoveryConfig(max_attempts=0))


if __name__ == "__main__":
    unittest.main()
