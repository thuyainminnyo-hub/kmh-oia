"""Orchestrate drift-triggered standard revalidation and lifecycle decisions."""
from dataclasses import dataclass
from .drift_revalidation import RevalidationTrigger
from .standard_revalidation import StandardRevalidation, StandardRevalidationEngine
from .standard_lifecycle import LifecycleDecision, StandardLifecycleManager
from .standardization_engine import OperatingStandard

@dataclass(frozen=True)
class RevalidationRun:
    trigger_id: str
    revalidation: StandardRevalidation
    lifecycle: LifecycleDecision

class RevalidationOrchestrator:
    def __init__(self, revalidator=None, lifecycle=None):
        self.revalidator = revalidator or StandardRevalidationEngine()
        self.lifecycle = lifecycle or StandardLifecycleManager()

    def run(self, trigger: RevalidationTrigger, standard: OperatingStandard, *, observed_effect: float, outcome_positive: bool) -> RevalidationRun:
        if trigger.status != "TRIGGERED":
            raise ValueError("only triggered revalidation requests can run")
        if trigger.standard_id != standard.id:
            raise ValueError("trigger and standard do not match")
        result = self.revalidator.evaluate(standard, observed_effect=observed_effect, evidence_id=trigger.evidence_id, outcome_positive=outcome_positive)
        decision = self.lifecycle.decide(result)
        return RevalidationRun(trigger.trigger_id, result, decision)
