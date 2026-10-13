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
    revised_conclusion: str | None = None
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
    if not isinstance(case, CriticalThinkingCase):
        raise TypeError("case must be a CriticalThinkingCase")

    # Dataclass annotations are not runtime validation. Fail closed on malformed
    # structured inputs instead of raising incidental AttributeError/TypeError or
    # accidentally treating an unknown scope as a supported bounded claim.
    schema_valid = (
        isinstance(case.correlation_id, str)
        and isinstance(case.original_claim, str)
        and type(case.evidence_count) is int
        and case.evidence_count >= 0
        and case.conclusion_scope in ("bounded", "universal", "unknown")
        and type(case.evidence_covers_entire_population) is bool
        and type(case.conclusion_qualified) is bool
        and (case.revised_conclusion is None or isinstance(case.revised_conclusion, str))
        and type(case.human_review_required) is bool
    )
    if not schema_valid:
        return CriticalThinkingQAResult(
            correlation_id=case.correlation_id if isinstance(case.correlation_id, str) else "",
            verdict="REWORK",
            original_claim=case.original_claim if isinstance(case.original_claim, str) else "",
            checks=("input_schema:fail",),
            reason="Structured QA input contains invalid field types or values.",
        )

    if not case.correlation_id.strip() or not case.original_claim.strip():
        return CriticalThinkingQAResult(
            correlation_id=case.correlation_id,
            verdict="REWORK",
            original_claim=case.original_claim,
            checks=("required_fields_present:fail",),
            reason="Correlation ID and original claim must be non-empty.",
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
        revised = (case.revised_conclusion or "").strip()
        if not revised or revised == case.original_claim.strip():
            checks.append("revised_conclusion_text:missing_or_unchanged")
            return CriticalThinkingQAResult(
                case.correlation_id, "REWORK", case.original_claim,
                tuple(checks),
                "Partial evidence cannot establish a universal conclusion. Supply a revised conclusion that narrows the claim; a qualification flag alone is insufficient.",
            )
        checks.append("revised_conclusion_text:provided")
        checks.append("revised_conclusion_semantics:human_review_required")
        return CriticalThinkingQAResult(
            case.correlation_id, "HUMAN_REVIEW", case.original_claim,
            tuple(checks),
            "A revised conclusion was supplied, but a human must verify that it genuinely narrows the universal claim before approval.",
        )

    checks.append("conclusion_scope_supported:pass")
    return CriticalThinkingQAResult(
        case.correlation_id, "PASS", case.original_claim,
        tuple(checks), "Deterministic contract checks passed.",
    )
