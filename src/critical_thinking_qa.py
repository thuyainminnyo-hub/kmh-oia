"""Deterministic contract adapter for Critical Thinking QA.

This module evaluates structured review metadata. It does not infer fallacies from
free text and does not call an LLM or external service.
"""
from dataclasses import dataclass
from typing import Literal

Verdict = Literal["PASS", "REWORK", "HUMAN_REVIEW"]


@dataclass(frozen=True)
class CriticalThinkingCase:
    correlation_id: str
    original_claim: str
    evidence_count: int
    conclusion_scope: Literal["bounded", "universal", "unknown"]
    evidence_covers_entire_population: bool = False
    conclusion_qualified: bool = False
    human_review_required: bool = False


@dataclass(frozen=True)
class CriticalThinkingQAResult:
    correlation_id: str
    verdict: Verdict
    original_claim: str
    checks: tuple[str, ...]
    reason: str


def evaluate_case(case: CriticalThinkingCase) -> CriticalThinkingQAResult:
    """Apply deterministic QA rules without rewriting the submitted claim."""
    if not case.correlation_id.strip() or not case.original_claim.strip():
        return CriticalThinkingQAResult(
            correlation_id=case.correlation_id,
            verdict="REWORK",
            original_claim=case.original_claim,
            checks=("required_fields_present:fail",),
            reason="Correlation ID and original claim must be non-empty.",
        )
    if case.evidence_count < 0:
        return CriticalThinkingQAResult(
            correlation_id=case.correlation_id,
            verdict="REWORK",
            original_claim=case.original_claim,
            checks=("evidence_count_non_negative:fail",),
            reason="Evidence count cannot be negative.",
        )
    checks = ["required_fields_present:pass", "original_claim_preserved:pass"]
    if case.human_review_required or case.conclusion_scope == "unknown":
        checks.append("human_review_gate:required")
        return CriticalThinkingQAResult(
            case.correlation_id, "HUMAN_REVIEW", case.original_claim,
            tuple(checks), "Case requires human judgment before approval.",
        )
    if (
        case.conclusion_scope == "universal"
        and not case.evidence_covers_entire_population
    ):
        checks.append("universal_claim_supported_by_full_population:fail")
        if not case.conclusion_qualified:
            checks.append("uncertainty_qualification:fail")
            return CriticalThinkingQAResult(
                case.correlation_id, "REWORK", case.original_claim,
                tuple(checks),
                "A universal conclusion is not established by partial evidence; qualify it or provide complete population evidence.",
            )
        checks.append("uncertainty_qualification:pass")
        return CriticalThinkingQAResult(
            case.correlation_id, "PASS", case.original_claim,
            tuple(checks),
            "Passed with qualification: partial evidence does not establish a universal conclusion.",
        )
    checks.append("conclusion_scope_supported:pass")
    return CriticalThinkingQAResult(
        case.correlation_id, "PASS", case.original_claim,
        tuple(checks), "Deterministic contract checks passed.",
    )
