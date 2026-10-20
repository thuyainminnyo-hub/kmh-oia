"""Deterministic admission gate for evidence-backed operating-loop learning.

Admission is conservative by design:
- required provenance must be present;
- raw observation is separate from interpretation;
- VERIFIED evidence needs a source and a raw observation;
- learning admission requires outcome-linked evidence;
- this gate evaluates supplied metadata and does not independently prove the source is authentic.
"""
from dataclasses import dataclass
from typing import Literal, Mapping


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


@dataclass(frozen=True)
class EvidenceAdmissionResult:
    decision: GateDecision
    evidence_status: EvidenceStatus
    learning_admitted: bool
    missing_fields: tuple[str, ...]
    reasons: tuple[str, ...]


class EvidenceAdmissionGate:
    """Check evidence admission requirements without fabricating evidence."""

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
        if status == "VERIFIED" and not missing and not request.source.strip():
            reasons.append("Verified evidence requires an identified source.")
        if status == "OUTCOME_LINKED" and not request.outcome_linked:
            reasons.append("OUTCOME_LINKED status requires explicit outcome linkage.")
        if request.outcome_linked and status != "OUTCOME_LINKED":
            reasons.append("Outcome linkage was asserted without OUTCOME_LINKED verification status.")

        admitted = (
            not missing
            and status == "OUTCOME_LINKED"
            and request.outcome_linked
        )
        if not admitted and not reasons:
            reasons.append(
                "Evidence is recorded but does not meet the external outcome-linked learning admission threshold."
            )
        if admitted:
            reasons.append(
                "Required fields are present and outcome linkage is explicitly declared; source authenticity remains externally dependent."
            )

        return EvidenceAdmissionResult(
            decision="ADMITTED" if admitted else "NOT_ADMITTED",
            evidence_status=status,
            learning_admitted=admitted,
            missing_fields=missing,
            reasons=tuple(reasons),
        )

    def evaluate_mapping(self, evidence: Mapping[str, str]) -> EvidenceAdmissionResult:
        """Evaluate a plain evidence mapping, marking absent values as empty."""
        status_text = evidence.get("verification_status", "UNKNOWN")
        allowed = {"UNKNOWN", "OBSERVED", "VERIFIED", "OUTCOME_LINKED"}
        if status_text not in allowed:
            status: EvidenceStatus = "UNKNOWN"
            status_reason = "Unrecognized verification_status; treated as UNKNOWN."
        else:
            status = status_text  # type: ignore[assignment]
            status_reason = ""
        outcome_linked = evidence.get("outcome_linked", "").strip().lower() == "true"
        request = EvidenceAdmissionRequest(
            execution_id=evidence.get("execution_id", ""),
            source=evidence.get("source", ""),
            raw_observation=evidence.get("raw_observation", ""),
            interpretation=evidence.get("interpretation", ""),
            verification_status=status,
            outcome_linked=outcome_linked,
        )
        result = self.evaluate(request)
        if not status_reason:
            return result
        return EvidenceAdmissionResult(
            decision=result.decision,
            evidence_status=result.evidence_status,
            learning_admitted=result.learning_admitted,
            missing_fields=result.missing_fields,
            reasons=(status_reason,) + result.reasons,
        )
