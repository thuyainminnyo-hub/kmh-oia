"""Stage 14 deterministic production runbook activation."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RunbookActivation:
    runbook_id: str
    phase: str
    activated: bool
    sections: tuple[str, ...]
    reason: str = ""


class ProductionRunbookActivator:
    """Model runbook activation readiness without executing production operations."""

    REQUIRED_SECTIONS = (
        "pre_deployment",
        "controlled_deployment",
        "health_verification",
        "stability_observation",
        "rollback",
        "incident_handling",
        "evidence_capture",
    )

    def prepare(self, *, runbook_id: str, sections: tuple[str, ...]) -> RunbookActivation:
        if not runbook_id.strip():
            raise ValueError("runbook_id is required")
        normalized = tuple(dict.fromkeys(section.strip() for section in sections if section.strip()))
        return RunbookActivation(runbook_id.strip(), "ready", False, normalized)

    def activate(self, state: RunbookActivation) -> RunbookActivation:
        if state.phase != "ready":
            raise RuntimeError("runbook activation requires ready state")
        missing = tuple(section for section in self.REQUIRED_SECTIONS if section not in state.sections)
        if missing:
            return RunbookActivation(
                state.runbook_id,
                "blocked",
                False,
                state.sections,
                "missing required sections: " + ", ".join(missing),
            )
        return RunbookActivation(
            state.runbook_id,
            "activated",
            True,
            state.sections,
            "runbook readiness validated",
        )

    def validate(self, state: RunbookActivation) -> None:
        if not state.activated or state.phase != "activated":
            raise RuntimeError("production runbook is not activated")
