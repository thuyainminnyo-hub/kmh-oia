"""Enforce active operating standards on commands before execution."""
from dataclasses import dataclass
from .standardization_engine import OperatingStandard

@dataclass(frozen=True)
class StandardCompliance:
    standard_id: str
    command_id: str
    compliant: bool
    evidence_required: bool = True
    reason: str = ""

class StandardEnforcementEngine:
    def check(self, standard: OperatingStandard, command_id: str, *, applied_rule: str, evidence_attached: bool = False) -> StandardCompliance:
        if standard.status != "ACTIVE":
            raise ValueError("only active standards can be enforced")
        if not command_id.strip():
            raise ValueError("command_id is required")
        compliant = applied_rule.strip() == standard.rule.strip()
        if standard.rule.strip() and not applied_rule.strip():
            compliant = False
        reason = "standard applied" if compliant else "command does not satisfy active standard"
        if not evidence_attached:
            reason += "; evidence required"
        return StandardCompliance(standard.id, command_id, compliant and evidence_attached, True, reason)
