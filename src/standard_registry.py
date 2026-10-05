"""Version registry and drift detection for operating standards."""
from dataclasses import dataclass
from .standardization_engine import OperatingStandard

@dataclass(frozen=True)
class StandardDrift:
    standard_id: str
    command_id: str
    expected_rule: str
    observed_rule: str
    drifted: bool
    reason: str

class StandardVersionRegistry:
    def __init__(self):
        self._standards = {}

    def register(self, standard: OperatingStandard):
        key = standard.source_adaptation_id
        versions = self._standards.setdefault(key, {})
        versions[standard.version] = standard
        return standard

    def versions(self, source_adaptation_id: str):
        return tuple(self._standards.get(source_adaptation_id, {}).values())

    def active(self, source_adaptation_id: str):
        active = [s for s in self.versions(source_adaptation_id) if s.status == "ACTIVE"]
        if len(active) > 1:
            raise ValueError("multiple active standard versions detected")
        return active[0] if active else None

    def detect_drift(self, standard: OperatingStandard, command_id: str, observed_rule: str):
        if standard.status != "ACTIVE":
            raise ValueError("only active standards can be monitored")
        if not command_id.strip():
            raise ValueError("command_id is required")
        expected = standard.rule.strip()
        observed = observed_rule.strip()
        drifted = expected != observed
        reason = "no standard drift" if not drifted else "observed execution rule differs from active standard"
        return StandardDrift(standard.id, command_id, expected, observed, drifted, reason)
