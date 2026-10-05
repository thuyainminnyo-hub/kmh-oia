"""Governed lifecycle for operating standards."""
from dataclasses import dataclass
from typing import Literal
from .standardization_engine import OperatingStandard, StandardizationEngine
from .standard_revalidation import StandardRevalidation

LifecycleAction = Literal["KEEP", "REVISE", "RETIRE"]

@dataclass(frozen=True)
class LifecycleDecision:
    standard_id: str
    action: LifecycleAction
    next_version: int
    reason: str

class StandardLifecycleManager:
    def __init__(self, standardization=None):
        self.standardization = standardization or StandardizationEngine()

    def decide(self, result):
        if result.verdict == "VALID":
            return LifecycleDecision(result.standard_id, "KEEP", 0, result.reason)
        if result.verdict == "REVISE":
            return LifecycleDecision(result.standard_id, "REVISE", 0, result.reason)
        return LifecycleDecision(result.standard_id, "RETIRE", 0, result.reason)

    def revise(self, standard, result, *, rule, expected_effect):
        if standard.status != "ACTIVE":
            raise ValueError("only active standards can be revised")
        if result.standard_id != standard.id or result.verdict != "REVISE":
            raise ValueError("revision requires a matching REVISE result")
        if not rule.strip() or not expected_effect.strip():
            raise ValueError("rule and expected_effect are required")
        return OperatingStandard("std:" + standard.source_adaptation_id + ":v" + str(standard.version + 1), standard.source_adaptation_id, rule, expected_effect, standard.version + 1, "PROPOSED")

    def retire(self, standard, result):
        if standard.status != "ACTIVE":
            raise ValueError("only active standards can be retired")
        if result.standard_id != standard.id or result.verdict != "RETIRE":
            raise ValueError("retirement requires a matching RETIRE result")
        return self.standardization.retire(standard)
