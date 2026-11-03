"""Bounded resilience primitives for provider adapters.

This module adds retry ceilings and a manually reset circuit breaker. It does
not silently switch providers or routes. A provider timeout must be enforced
by the concrete adapter and surfaced as TimeoutError.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from src.model_gateway import ModelProvider, ModelResponse


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0

    def __post_init__(self) -> None:
        if (
            isinstance(self.failure_threshold, bool)
            or not isinstance(self.failure_threshold, int)
            or self.failure_threshold <= 0
        ):
            raise ValueError("failure_threshold must be a positive integer")
        if not isinstance(self.state, CircuitState):
            raise ValueError("state must be CircuitState")
        if (
            isinstance(self.consecutive_failures, bool)
            or not isinstance(self.consecutive_failures, int)
            or self.consecutive_failures < 0
        ):
            raise ValueError("consecutive_failures must be a non-negative integer")

    def allow_request(self) -> bool:
        return self.state is CircuitState.CLOSED

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def reset(self) -> None:
        """Explicit operator-controlled reset; no automatic half-open probe."""
        self.consecutive_failures = 0
        self.state = CircuitState.CLOSED


class RetryingModelProvider:
    """Retry only transient failures, with a strict attempt ceiling."""

    TRANSIENT_ERRORS = (TimeoutError, ConnectionError)

    def __init__(
        self,
        provider: ModelProvider,
        max_attempts: int = 2,
        circuit_breaker: CircuitBreaker | None = None,
        on_retry: Callable[[int, str], None] | None = None,
    ) -> None:
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
            raise ValueError("max_attempts must be an integer")
        if max_attempts < 1 or max_attempts > 3:
            raise ValueError("max_attempts must be between 1 and 3")
        if not callable(getattr(provider, "generate", None)):
            raise ValueError("provider must implement generate(request)")
        self._provider = provider
        self._max_attempts = max_attempts
        self._breaker = circuit_breaker or CircuitBreaker()
        self._on_retry = on_retry

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        return self._breaker

    def generate(self, request) -> ModelResponse:
        if not self._breaker.allow_request():
            raise RuntimeError("provider circuit is open")
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = self._provider.generate(request)
            except self.TRANSIENT_ERRORS as exc:
                if attempt >= self._max_attempts:
                    self._breaker.record_failure()
                    raise
                if self._on_retry is not None:
                    self._on_retry(attempt, type(exc).__name__)
            except Exception:
                # Non-transient errors are not retried, but count toward the
                # circuit threshold because the provider attempt failed.
                self._breaker.record_failure()
                raise
            else:
                self._breaker.record_success()
                return response
        raise RuntimeError("retry loop exhausted unexpectedly")
