"""Stage 14 deterministic incident controller."""
from dataclasses import dataclass

@dataclass(frozen=True)
class IncidentState:
    incident_id: str
    severity: str
    phase: str
    reason: str
    evidence_captured: bool = False

class IncidentController:
    """Model incident lifecycle and evidence capture without live operations."""
    SEVERITIES = {"low", "medium", "high", "critical"}
    def open(self, *, incident_id: str, severity: str, reason: str) -> IncidentState:
        if not incident_id.strip(): raise ValueError("incident_id is required")
        if severity not in self.SEVERITIES: raise ValueError("invalid severity")
        if not reason.strip(): raise ValueError("reason is required")
        return IncidentState(incident_id.strip(), severity, "open", reason.strip())
    def capture_evidence(self, state: IncidentState) -> IncidentState:
        if state.phase != "open": raise RuntimeError("evidence capture requires open incident")
        return IncidentState(state.incident_id, state.severity, "evidence_captured", state.reason, True)
    def resolve(self, state: IncidentState, *, validated: bool) -> IncidentState:
        if state.phase != "evidence_captured": raise RuntimeError("resolution requires captured evidence")
        if not validated: raise RuntimeError("incident resolution requires validation")
        return IncidentState(state.incident_id, state.severity, "resolved", state.reason, True)
