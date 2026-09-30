"""Stage 14 deterministic recovery controller."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryState:
    operation: str
    attempts: int
    max_attempts: int
    phase: str
    reason: str = ""


class RecoveryController:
    """Model bounded recovery decisions without executing production operations."""

    def start(self, *, operation: str, max_attempts: int = 3) -> RecoveryState:
        if not operation.strip():
            raise ValueError("operation is required")
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        return RecoveryState(operation.strip(), 0, max_attempts, "ready")

    def attempt(self, state: RecoveryState, *, succeeded: bool) -> RecoveryState:
        if state.phase in {"recovered", "exhausted"}:
            raise RuntimeError(f"recovery cannot continue from phase: {state.phase}")
        attempts = state.attempts + 1
        if succeeded:
            return RecoveryState(state.operation, attempts, state.max_attempts, "recovered", "operation recovered")
        if attempts >= state.max_attempts:
            return RecoveryState(state.operation, attempts, state.max_attempts, "exhausted", "recovery budget exhausted")
        return RecoveryState(state.operation, attempts, state.max_attempts, "retrying", "retry permitted")

    def validate(self, state: RecoveryState, *, health_passed: bool) -> None:
        if state.phase != "recovered":
            raise RuntimeError("recovery validation requires a recovered operation")
        if not health_passed:
            raise RuntimeError("recovery validation failed: health gate failed")
