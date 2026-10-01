"""Stage 15 deterministic stabilization observation controller."""
from dataclasses import dataclass


@dataclass(frozen=True)
class StabilizationState:
    release_id: str
    windows_observed: int
    healthy_windows: int
    required_healthy_windows: int
    stable: bool
    phase: str
    reason: str = ""


class StabilizationController:
    """Evaluate explicit observation windows against an operator-supplied gate."""

    def start(self, *, release_id: str, required_healthy_windows: int) -> StabilizationState:
        if not isinstance(release_id, str) or not release_id.strip():
            raise ValueError("release_id is required")
        if (not isinstance(required_healthy_windows, int)
                or isinstance(required_healthy_windows, bool)
                or required_healthy_windows < 1):
            raise ValueError("required_healthy_windows must be a positive integer")
        return StabilizationState(
            release_id.strip(), 0, 0, required_healthy_windows, False, "observing"
        )

    def observe(self, state: StabilizationState, *, healthy: bool) -> StabilizationState:
        if state.phase != "observing":
            raise RuntimeError("stabilization is not accepting observations")
        if not isinstance(healthy, bool):
            raise ValueError("healthy observation must be boolean")
        windows = state.windows_observed + 1
        healthy_windows = state.healthy_windows + (1 if healthy else 0)
        stable = healthy_windows >= state.required_healthy_windows
        return StabilizationState(
            state.release_id, windows, healthy_windows,
            state.required_healthy_windows, stable,
            "stable" if stable else "observing",
            "required healthy observation windows reached" if stable
            else "stabilization gate not yet satisfied",
        )

    def validate(self, state: StabilizationState) -> None:
        if state.phase != "stable" or not state.stable:
            raise RuntimeError("stabilization gate is not satisfied")
