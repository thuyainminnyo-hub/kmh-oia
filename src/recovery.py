"""Deterministic recovery controls for the KMH OIA runtime."""

from dataclasses import dataclass
from time import monotonic
from typing import Callable, Protocol, TypeVar


T = TypeVar("T")


class RecoveryError(RuntimeError):
    """Base error for controlled runtime recovery failures."""


class RetryableExecutionError(RecoveryError):
    """Signal that an operation may be retried within its retry budget."""


class CancelledError(RecoveryError):
    """Signal that execution was cancelled before or between attempts."""


class RecoveryPolicy(Protocol):
    """Boundary for bounded retry, timeout, and cancellation decisions."""

    def run(self, operation: Callable[[], T]) -> T: ...


@dataclass(frozen=True)
class RecoveryConfig:
    max_attempts: int = 1
    timeout_seconds: float | None = None
    is_cancelled: Callable[[], bool] | None = None


class DeterministicRecoveryPolicy:
    """Bound retries and observe cancellation/deadline without background threads."""

    def __init__(self, config: RecoveryConfig | None = None) -> None:
        self.config = config or RecoveryConfig()
        if self.config.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.config.timeout_seconds is not None and self.config.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    def run(self, operation: Callable[[], T]) -> T:
        started = monotonic()
        for attempt in range(1, self.config.max_attempts + 1):
            self._check_cancelled()
            self._check_timeout(started)
            try:
                result = operation()
                self._check_timeout(started)
                return result
            except RetryableExecutionError:
                if attempt >= self.config.max_attempts:
                    raise
                self._check_cancelled()
                self._check_timeout(started)
        raise RuntimeError("recovery policy exited without a result")

    def _check_cancelled(self) -> None:
        if self.config.is_cancelled and self.config.is_cancelled():
            raise CancelledError("execution cancelled")

    def _check_timeout(self, started: float) -> None:
        if self.config.timeout_seconds is not None and monotonic() - started > self.config.timeout_seconds:
            raise TimeoutError("execution timeout exceeded")
