"""Governed trust classification for verified runtime executions."""
from dataclasses import dataclass
from typing import Mapping

from src.real_execution_verification import VerificationResult


TrustLevel = str


@dataclass(frozen=True)
class TrustDecision:
    execution_id: str
    level: TrustLevel
    trusted: bool
    reason: str
    checks: Mapping[str, bool]


class RuntimeTrustEngine:
    """Classify verification results without bypassing governance."""

    def decide(
        self,
        verification: VerificationResult,
        *,
        governance_approved: bool = False,
    ) -> TrustDecision:
        if not verification.verified:
            return TrustDecision(
                verification.execution_id,
                "UNPROVEN",
                False,
                "Execution proof is incomplete or failed verification.",
                verification.checks,
            )
        if not governance_approved:
            return TrustDecision(
                verification.execution_id,
                "CONDITIONAL",
                False,
                "Execution proof is complete, but governance approval is required for trusted classification.",
                verification.checks,
            )
        return TrustDecision(
            verification.execution_id,
            "PROVEN",
            True,
            "Execution proof is verified and governance-approved.",
            verification.checks,
        )
