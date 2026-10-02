"""Repository-level deterministic autonomy policy evaluation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AutonomyDecision:
    allowed: bool
    reason: str


class AutonomyPolicy:
    """Evaluate exact action and scope allowlists; does not execute actions."""

    def __init__(self, allowed_actions: set[str], allowed_scopes: set[str]) -> None:
        self._actions = frozenset(allowed_actions)
        self._scopes = frozenset(allowed_scopes)

    def evaluate(self, action: str, scope: str) -> AutonomyDecision:
        if not isinstance(action, str) or not action.strip():
            return AutonomyDecision(False, "action must be non-empty")
        if not isinstance(scope, str) or not scope.strip():
            return AutonomyDecision(False, "scope must be non-empty")
        if action not in self._actions:
            return AutonomyDecision(False, "action is not allowlisted")
        if scope not in self._scopes:
            return AutonomyDecision(False, "scope is not allowlisted")
        return AutonomyDecision(True, "action and scope are allowlisted")
