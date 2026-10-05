"""Connect active operating standards to runtime execution decisions."""
from dataclasses import dataclass
from .standard_control_plane import StandardControlPlane
from .standard_enforcement import StandardCompliance
from .standardization_engine import OperatingStandard

@dataclass(frozen=True)
class RuntimeStandardCheck:
    command_id: str
    standard_id: str
    allowed: bool
    compliance: StandardCompliance

class StandardRuntimeBridge:
    def __init__(self, control_plane: StandardControlPlane | None = None) -> None:
        self.control_plane = control_plane or StandardControlPlane()

    def authorize(self, standard: OperatingStandard, command_id: str, *, applied_rule: str) -> RuntimeStandardCheck:
        compliance = self.control_plane.enforce(standard, command_id, applied_rule=applied_rule, evidence_attached=True)
        if not compliance.compliant:
            raise PermissionError(f"command {command_id} does not satisfy active standard {standard.id}")
        return RuntimeStandardCheck(command_id, standard.id, True, compliance)
