"""Stage 14 deterministic production change control."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ChangeControlState:
    change_id: str
    phase: str
    approved: bool
    validated: bool
    reason: str = ""


class ProductionChangeController:
    """Model approved change readiness without executing live infrastructure changes."""

    def submit(self, *, change_id: str) -> ChangeControlState:
        if not change_id.strip():
            raise ValueError("change_id is required")
        return ChangeControlState(change_id.strip(), "submitted", False, False)

    def approve(self, state: ChangeControlState, *, approved: bool) -> ChangeControlState:
        if state.phase != "submitted":
            raise RuntimeError("approval requires submitted state")
        if not approved:
            return ChangeControlState(
                state.change_id, "rejected", False, False, "change approval rejected"
            )
        return ChangeControlState(
            state.change_id, "approved", True, False, "change approved"
        )

    def validate(self, state: ChangeControlState, *, validation_passed: bool) -> ChangeControlState:
        if state.phase != "approved" or not state.approved:
            raise RuntimeError("validation requires approved change")
        if not validation_passed:
            return ChangeControlState(
                state.change_id, "validation_failed", True, False, "change validation failed"
            )
        return ChangeControlState(
            state.change_id, "execution_ready", True, True, "change validated"
        )

    def require_execution_ready(self, state: ChangeControlState) -> None:
        if state.phase != "execution_ready" or not state.approved or not state.validated:
            raise RuntimeError("change is not execution-ready")
