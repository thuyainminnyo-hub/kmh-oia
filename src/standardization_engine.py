"""Promote validated improvements into versioned operating standards."""
from dataclasses import dataclass
from typing import Literal
from .adaptation_validation import AdaptationExperiment

StandardStatus = Literal["PROPOSED", "APPROVED", "ACTIVE", "RETIRED"]

@dataclass(frozen=True)
class OperatingStandard:
    id: str
    source_adaptation_id: str
    rule: str
    expected_effect: str
    version: int = 1
    status: StandardStatus = "PROPOSED"

class StandardizationEngine:
    def propose(self, experiment: AdaptationExperiment, *, rule: str, expected_effect: str) -> OperatingStandard:
        if experiment.verdict != "IMPROVED":
            raise ValueError("only improved experiments can become standards")
        if not rule.strip() or not expected_effect.strip():
            raise ValueError("rule and expected_effect are required")
        return OperatingStandard(f"std:{experiment.adaptation_id}:v1", experiment.adaptation_id, rule, expected_effect)

    def approve(self, standard: OperatingStandard) -> OperatingStandard:
        if standard.status != "PROPOSED":
            raise ValueError("only proposed standards can be approved")
        return OperatingStandard(standard.id, standard.source_adaptation_id, standard.rule, standard.expected_effect, standard.version, "APPROVED")

    def activate(self, standard: OperatingStandard) -> OperatingStandard:
        if standard.status != "APPROVED":
            raise ValueError("only approved standards can be activated")
        return OperatingStandard(standard.id, standard.source_adaptation_id, standard.rule, standard.expected_effect, standard.version, "ACTIVE")

    def retire(self, standard: OperatingStandard) -> OperatingStandard:
        if standard.status != "ACTIVE":
            raise ValueError("only active standards can be retired")
        return OperatingStandard(standard.id, standard.source_adaptation_id, standard.rule, standard.expected_effect, standard.version, "RETIRED")
