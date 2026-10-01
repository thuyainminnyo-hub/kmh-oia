"""Stage 15 controlled autonomy readiness evidence gate."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AutonomyReadiness:
    scope: str
    evidence: tuple[str, ...]
    missing: tuple[str, ...]
    phase: str
    production_authorized: bool = False


class ControlledAutonomyReadinessGate:
    """Assess bounded readiness evidence without granting production authority."""

    REQUIRED_EVIDENCE = (
        "bounded_scope",
        "human_oversight",
        "tool_allowlist",
        "rollback_plan",
        "monitoring",
        "evaluation",
        "incident_response",
    )

    def assess(self, *, scope: str, evidence: dict[str, str]) -> AutonomyReadiness:
        if not isinstance(scope, str) or not scope.strip():
            raise ValueError("bounded autonomy scope is required")
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a mapping")
        for key, value in evidence.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("evidence keys and values must be strings")
        supplied = tuple(sorted(
            key for key, value in evidence.items()
            if key in self.REQUIRED_EVIDENCE and value.strip()
        ))
        missing = tuple(key for key in self.REQUIRED_EVIDENCE if key not in supplied)
        return AutonomyReadiness(
            scope.strip(), supplied, missing,
            "evidence_ready_for_review" if not missing else "blocked",
            False,
        )

    def require_ready(self, result: AutonomyReadiness) -> None:
        if not isinstance(result, AutonomyReadiness) or result.phase != "evidence_ready_for_review" or result.missing:
            raise RuntimeError("controlled autonomy readiness evidence is incomplete")
        if result.production_authorized:
            raise RuntimeError("repository evidence cannot grant production authorization")
