"""Stage 14 deterministic controlled production promotion."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionState:
    release_id: str
    phase: str
    promoted: bool
    reason: str = ""


class ControlledProductionPromotion:
    """Model health-gated production promotion without changing live infrastructure."""

    def start(self, *, release_id: str) -> PromotionState:
        if not release_id.strip():
            raise ValueError("release_id is required")
        return PromotionState(release_id.strip(), "ready", False)

    def promote(
        self, state: PromotionState, *, health_passed: bool
    ) -> PromotionState:
        if state.phase != "ready":
            raise RuntimeError("promotion requires ready state")
        if not health_passed:
            return PromotionState(
                state.release_id, "blocked", False, "health gate failed"
            )
        return PromotionState(
            state.release_id, "promoted", True, "health gate passed"
        )

    def validate(self, state: PromotionState) -> None:
        if not state.promoted or state.phase != "promoted":
            raise RuntimeError("production promotion is not validated")
