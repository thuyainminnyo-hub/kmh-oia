"""Revalidate active standards against real execution outcomes."""
from dataclasses import dataclass
from typing import Literal
from .standardization_engine import OperatingStandard

RevalidationVerdict = Literal["VALID", "REVISE", "RETIRE"]

@dataclass(frozen=True)
class StandardRevalidation:
    standard_id: str
    observed_effect: float
    expected_effect: str
    verdict: RevalidationVerdict
    evidence_id: str
    reason: str

class StandardRevalidationEngine:
    def evaluate(self, standard: OperatingStandard, *, observed_effect: float, evidence_id: str, outcome_positive: bool) -> StandardRevalidation:
        if standard.status != "ACTIVE":
            raise ValueError("only active standards can be revalidated")
        if not evidence_id.strip():
            raise ValueError("evidence_id is required")
        if observed_effect < 0:
            raise ValueError("observed_effect must be non-negative")
        if outcome_positive:
            verdict, reason = "VALID", "Real execution evidence supports the active standard."
        elif observed_effect == 0:
            verdict, reason = "REVISE", "Real execution produced no measurable improvement."
        else:
            verdict, reason = "RETIRE", "Real execution evidence indicates the standard is harmful."
        return StandardRevalidation(standard.id, observed_effect, standard.expected_effect, verdict, evidence_id, reason)

    def should_keep(self, result: StandardRevalidation) -> bool:
        return result.verdict == "VALID"

    def should_change(self, result: StandardRevalidation) -> bool:
        return result.verdict in {"REVISE", "RETIRE"}
