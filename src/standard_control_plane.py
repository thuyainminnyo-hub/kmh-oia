"""Single control-plane facade for operating-standard governance."""
from dataclasses import dataclass
from .standard_registry import StandardVersionRegistry, StandardDrift
from .standard_enforcement import StandardEnforcementEngine, StandardCompliance
from .drift_revalidation import DriftRevalidationTrigger, RevalidationTrigger
from .revalidation_orchestrator import RevalidationOrchestrator, RevalidationRun

@dataclass(frozen=True)
class StandardControlResult:
    compliance: StandardCompliance
    drift: StandardDrift | None
    trigger: RevalidationTrigger | None
    revalidation: RevalidationRun | None

class StandardControlPlane:
    """Coordinate registry, enforcement, drift, trigger and revalidation boundaries."""
    def __init__(self, registry=None, enforcement=None, triggers=None, orchestrator=None):
        self.registry = registry or StandardVersionRegistry()
        self.enforcement = enforcement or StandardEnforcementEngine()
        self.triggers = triggers or DriftRevalidationTrigger()
        self.orchestrator = orchestrator or RevalidationOrchestrator()

    def register(self, standard):
        return self.registry.register(standard)

    def enforce(self, standard, command_id, *, applied_rule, evidence_attached=False):
        return self.enforcement.check(standard, command_id, applied_rule=applied_rule, evidence_attached=evidence_attached)

    def observe(self, standard, command_id, *, applied_rule, evidence_id):
        compliance = self.enforce(standard, command_id, applied_rule=applied_rule, evidence_attached=True)
        drift = self.registry.detect_drift(standard, command_id, applied_rule)
        trigger = self.triggers.create(drift, evidence_id=evidence_id) if drift.drifted else None
        return StandardControlResult(compliance, drift, trigger, None)

    def revalidate(self, control_result, standard, *, observed_effect, outcome_positive):
        if control_result.trigger is None:
            raise ValueError("revalidation requires a drift trigger")
        run = self.orchestrator.run(control_result.trigger, standard, observed_effect=observed_effect, outcome_positive=outcome_positive)
        return StandardControlResult(control_result.compliance, control_result.drift, control_result.trigger, run)
