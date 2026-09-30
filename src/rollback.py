"""Stage 14 deterministic rollback controller."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RollbackState:
    release_id: str
    previous_release_id: str
    phase: str
    reason: str
    evidence_preserved: bool = False


class RollbackController:
    """Model rollback readiness and execution without changing production traffic."""

    def prepare(self, *, release_id: str, previous_release_id: str) -> RollbackState:
        if not release_id.strip():
            raise ValueError("release_id is required")
        if not previous_release_id.strip():
            raise ValueError("previous_release_id is required")
        if release_id.strip() == previous_release_id.strip():
            raise ValueError("previous release must differ from current release")
        return RollbackState(release_id.strip(), previous_release_id.strip(), "ready", "")

    def execute(self, state: RollbackState, *, trigger: str) -> RollbackState:
        if not trigger.strip():
            raise ValueError("rollback trigger is required")
        if state.phase != "ready":
            raise RuntimeError(f"rollback cannot execute from phase: {state.phase}")
        return RollbackState(
            state.release_id,
            state.previous_release_id,
            "rolled_back",
            trigger.strip(),
            evidence_preserved=True,
        )

    def validate(self, state: RollbackState, *, previous_release_available: bool, health_passed: bool) -> None:
        if state.phase != "rolled_back":
            raise RuntimeError("rollback validation requires completed rollback")
        if not state.evidence_preserved:
            raise RuntimeError("rollback validation requires preserved evidence")
        if not previous_release_available:
            raise RuntimeError("rollback validation failed: previous release unavailable")
        if not health_passed:
            raise RuntimeError("rollback validation failed: health gate failed")
