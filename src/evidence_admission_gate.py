"""Deterministic admission gate for evidence-backed operating-loop learning.

The gate validates supplied metadata and requires independent verification
signals before admitting learning. It does not itself authenticate a provider.
"""
from dataclasses import dataclass
from typing import Literal, Mapping

from src.trusted_source_receipt import ReceiptVerificationResult


GateDecision = Literal["ADMITTED", "NOT_ADMITTED"]
EvidenceStatus = Literal["UNKNOWN", "OBSERVED", "VERIFIED", "OUTCOME_LINKED"]


@dataclass(frozen=True)
class EvidenceAdmissionRequest:
    execution_id: str
    source: str
    raw_observation: str
    interpretation: str = ""
    verification_status: EvidenceStatus = "UNKNOWN"
    outcome_linked: bool = False
    trusted_receipt_verification: ReceiptVerificationResult | None = None


@dataclass(frozen=True)
class EvidenceAdmissionResult:
    decision: GateDecision
    evidence_status: EvidenceStatus
    learning_admitted: bool
    missing_fields: tuple[str, ...]
    reasons: tuple[str, ...]


class EvidenceAdmissionGate:
    """Admit learning only when provenance, authentication, and attribution agree."""

    def evaluate(self, request: EvidenceAdmissionRequest) -> EvidenceAdmissionResult:
        missing = tuple(
            name
            for name, value in (
                ("execution_id", request.execution_id),
                ("source", request.source),
                ("raw_observation", request.raw_observation),
            )
            if not isinstance(value, str) or not value.strip()
        )
        reasons: list[str] = []
        status = request.verification_status

        if missing:
            reasons.append("Required provenance or raw observation is missing.")
        if status not in {"UNKNOWN", "OBSERVED", "VERIFIED", "OUTCOME_LINKED"}:
            reasons.append("Unrecognized verification_status; treated as UNKNOWN.")
            status = "UNKNOWN"
        if status == "OUTCOME_LINKED" and not request.outcome_linked:
            reasons.append("OUTCOME_LINKED status requires explicit outcome linkage.")
        if request.outcome_linked and status != "OUTCOME_LINKED":
            reasons.append("Outcome linkage was asserted without OUTCOME_LINKED verification status.")
        receipt_result = request.trusted_receipt_verification
        trusted_receipt_verified = (
            isinstance(receipt_result, ReceiptVerificationResult)
            and receipt_result.verified
            and receipt_result.execution_id == request.execution_id
            and f"{receipt_result.provider_name}:{receipt_result.source_record_id}" == request.source
            and receipt_result.raw_observation == request.raw_observation
        )
        if status == "OUTCOME_LINKED" and not trusted_receipt_verified:
            reasons.append(
                "Trusted source receipt verifier result is missing, unverified, or does not match source/execution/raw observation."
            )

        admitted = (
            not missing
            and status == "OUTCOME_LINKED"
            and request.outcome_linked
            and trusted_receipt_verified
        )
        if not admitted and not reasons:
            reasons.append(
                "Evidence is present but does not meet the outcome-linked learning admission threshold."
            )
        if admitted:
            reasons.append(
                "Required fields match a successful trusted receipt verification and execution-attribution result."
            )

        return EvidenceAdmissionResult(
            decision="ADMITTED" if admitted else "NOT_ADMITTED",
            evidence_status=status,
            learning_admitted=admitted,
            missing_fields=missing,
            reasons=tuple(reasons),
        )

    def evaluate_mapping(self, evidence: Mapping[str, str]) -> EvidenceAdmissionResult:
        """Evaluate supplied metadata; missing or invalid fields fail closed."""
        status_text = evidence.get("verification_status", "UNKNOWN")
        allowed = {"UNKNOWN", "OBSERVED", "VERIFIED", "OUTCOME_LINKED"}
        status: EvidenceStatus = status_text if status_text in allowed else "UNKNOWN"  # type: ignore[assignment]
        outcome_linked = evidence.get("outcome_linked", "").strip().lower() == "true"
        request = EvidenceAdmissionRequest(
            execution_id=evidence.get("execution_id", ""),
            source=evidence.get("source", ""),
            raw_observation=evidence.get("raw_observation", ""),
            interpretation=evidence.get("interpretation", ""),
            verification_status=status,
            outcome_linked=outcome_linked,
            trusted_receipt_verification=None,
        )
        result = self.evaluate(request)
        if status_text in allowed:
            return result
        return EvidenceAdmissionResult(
            decision=result.decision,
            evidence_status=result.evidence_status,
            learning_admitted=result.learning_admitted,
            missing_fields=result.missing_fields,
            reasons=("Unrecognized verification_status; treated as UNKNOWN.",) + result.reasons,
        )
