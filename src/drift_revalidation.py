"""Turn detected standard drift into an explicit revalidation request."""
from dataclasses import dataclass
from typing import Literal
from .standard_registry import StandardDrift

TriggerStatus = Literal["NOT_TRIGGERED", "TRIGGERED", "RESOLVED"]

@dataclass(frozen=True)
class RevalidationTrigger:
    trigger_id: str
    standard_id: str
    command_id: str
    evidence_id: str
    reason: str
    status: TriggerStatus

class DriftRevalidationTrigger:
    def create(self, drift: StandardDrift, *, evidence_id: str) -> RevalidationTrigger:
        if not drift.drifted:
            raise ValueError("revalidation trigger requires detected drift")
        if not evidence_id.strip():
            raise ValueError("evidence_id is required")
        trigger_id = f"reval:{drift.standard_id}:{drift.command_id}"
        return RevalidationTrigger(trigger_id, drift.standard_id, drift.command_id, evidence_id, drift.reason, "TRIGGERED")

    def resolve(self, trigger: RevalidationTrigger) -> RevalidationTrigger:
        if trigger.status != "TRIGGERED":
            raise ValueError("only triggered requests can be resolved")
        return RevalidationTrigger(trigger.trigger_id, trigger.standard_id, trigger.command_id, trigger.evidence_id, trigger.reason, "RESOLVED")
