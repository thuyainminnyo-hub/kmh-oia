"""Feed completed runtime evidence back into standard governance."""
from dataclasses import dataclass

from src.standard_control_plane import StandardControlPlane, StandardControlResult
from src.standardization_engine import OperatingStandard


@dataclass(frozen=True)
class RuntimeStandardFeedback:
    command_id: str
    evidence_id: str
    control_result: StandardControlResult


class RuntimeStandardFeedbackEngine:
    """Turn post-execution evidence into a control-plane observation."""

    def __init__(self, control_plane: StandardControlPlane | None = None) -> None:
        self.control_plane = control_plane or StandardControlPlane()

    def capture(
        self,
        standard: OperatingStandard,
        command_id: str,
        *,
        applied_rule: str,
        evidence_id: str,
    ) -> RuntimeStandardFeedback:
        if not evidence_id.strip():
            raise ValueError("evidence_id is required")
        result = self.control_plane.observe(
            standard,
            command_id,
            applied_rule=applied_rule,
            evidence_id=evidence_id,
        )
        return RuntimeStandardFeedback(command_id, evidence_id, result)
