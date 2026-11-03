import unittest
from decimal import Decimal

from src.ai_contracts import AIRequest, TaskClass
from src.model_gateway import ModelResponse, ModelUsage
from src.resilience import CircuitBreaker, CircuitState, RetryingModelProvider


def request():
    return AIRequest(
        request_id="r1",
        session_id="s1",
        task_class=TaskClass.CODE_REVIEW,
        input_text="review",
        route_id="test",
        estimated_input_tokens=10,
        max_output_tokens=10,
    )


class SequenceProvider:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class CircuitBreakerTests(unittest.TestCase):
    def test_opens_at_failure_threshold(self):
        breaker = CircuitBreaker(failure_threshold=2)
        breaker.record_failure()
        self.assertTrue(breaker.allow_request())
        breaker.record_failure()
        self.assertEqual(breaker.state, CircuitState.OPEN)
        self.assertFalse(breaker.allow_request())

    def test_success_resets_failure_count(self):
        breaker = CircuitBreaker(failure_threshold=2)
        breaker.record_failure()
        breaker.record_success()
        self.assertEqual(breaker.consecutive_failures, 0)
        self.assertTrue(breaker.allow_request())

    def test_operator_reset_closes_circuit(self):
        breaker = CircuitBreaker(failure_threshold=1)
        breaker.record_failure()
        breaker.reset()
        self.assertEqual(breaker.state, CircuitState.CLOSED)
        self.assertTrue(breaker.allow_request())

    def test_invalid_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            CircuitBreaker(failure_threshold=0)


class RetryingProviderTests(unittest.TestCase):
    def test_transient_error_retries_then_succeeds(self):
        expected = ModelResponse("ok", ModelUsage(2, 2, Decimal("0")))
        provider = SequenceProvider([TimeoutError(), expected])
        retry_events = []
        wrapper = RetryingModelProvider(
            provider, max_attempts=2,
            on_retry=lambda attempt, kind: retry_events.append((attempt, kind)),
        )
        self.assertEqual(wrapper.generate(request()), expected)
        self.assertEqual(provider.calls, 2)
        self.assertEqual(retry_events, [(1, "TimeoutError")])

    def test_retry_attempts_are_bounded(self):
        provider = SequenceProvider([TimeoutError(), TimeoutError(), TimeoutError()])
        wrapper = RetryingModelProvider(provider, max_attempts=2)
        with self.assertRaises(TimeoutError):
            wrapper.generate(request())
        self.assertEqual(provider.calls, 2)
        self.assertEqual(wrapper.circuit_breaker.consecutive_failures, 1)

    def test_non_transient_error_is_not_retried(self):
        provider = SequenceProvider([ValueError("bad request"), "unused"])
        wrapper = RetryingModelProvider(provider, max_attempts=3)
        with self.assertRaises(ValueError):
            wrapper.generate(request())
        self.assertEqual(provider.calls, 1)

    def test_open_circuit_blocks_provider_call(self):
        provider = SequenceProvider([TimeoutError()])
        breaker = CircuitBreaker(failure_threshold=1)
        wrapper = RetryingModelProvider(provider, circuit_breaker=breaker)
        with self.assertRaisesRegex(RuntimeError, "circuit is open"):
            wrapper.generate(request())
        self.assertEqual(provider.calls, 0)

    def test_max_attempts_is_limited_to_three(self):
        provider = SequenceProvider(["unused"])
        with self.assertRaisesRegex(ValueError, "between 1 and 3"):
            RetryingModelProvider(provider, max_attempts=4)


if __name__ == "__main__":
    unittest.main()
