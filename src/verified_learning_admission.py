"""Bind learning eligibility to evidence already admitted by the live runtime.

This module does not authenticate providers by itself. It accepts only an
ExecutionRecord whose runtime path carries a matching trusted receipt result
and an OUTCOME_LINKED admission result. Treat these Python objects as internal
application contracts, not as an unforgeable security boundary.
"""
from dataclasses import dataclass

from src.decision_outcome_evaluator import DecisionOutcome
from src.evidence_admission_gate import EvidenceAdmissionResult
from src.live_runtime_bridge import ExecutionRecord
from src.trusted_source_receipt import ReceiptVerificationResult


@dataclass(frozen=True)
class VerifiedLearningAdmission:
    """Immutable, execution-bound evidence needed to qualify a learning record."""

    decision_id: str
    command_id: str
    execution_id: str
    trace_id: str
    evidence_id: str
    policy_version: str
    provider_name: str
    source_record_id: str
    verification_method: str
    receipt_content_hash: str
    admission_reasons: tuple[str, ...]

    @classmethod
    def from_execution(
        cls,
        outcome: DecisionOutcome,
        execution: ExecutionRecord,
        *,
        evidence_id: str,
        policy_version: str,
    ) -> "VerifiedLearningAdmission":
        """Build a receipt-bound summary; IDs and policy version remain caller references.

        This factory cannot authenticate evidence_id or policy_version without an
        authoritative evidence/policy registry. Consumers must not treat those
        two fields as independently verified by this method.
        """
        for name, value in (
            ("evidence_id", evidence_id),
            ("policy_version", policy_version),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")

        loop = execution.operating_loop
        admission = execution.admission
        receipt = execution.trusted_receipt_verification

        if execution.final_status != "LEARNED":
            raise ValueError("verified learning requires a LEARNED execution")
        if outcome.command_id != execution.command_id:
            raise ValueError("outcome command_id does not match execution")
        if loop is None:
            raise ValueError("operating-loop trace is required for verified learning")
        if loop.decision_id != outcome.decision_id or loop.command_id != outcome.command_id:
            raise ValueError("decision/command trace does not match the outcome")
        if not loop.source_decision_id or loop.source_decision_id != outcome.decision_id:
            raise ValueError("execution must be traceable to the source decision")
        if not loop.trace_id.strip() or not loop.execution_id.strip():
            raise ValueError("trace_id and execution_id are required")
        if not isinstance(admission, EvidenceAdmissionResult):
            raise ValueError("evidence admission result is required")
        if (
            admission.decision != "ADMITTED"
            or not admission.learning_admitted
            or admission.evidence_status != "OUTCOME_LINKED"
        ):
            raise ValueError("evidence admission must be ADMITTED and OUTCOME_LINKED")
        if (
            loop.learning_status != "ADMITTED"
            or loop.evidence_status != "OUTCOME_LINKED"
        ):
            raise ValueError("operating-loop trace does not confirm admitted outcome evidence")
        if not isinstance(receipt, ReceiptVerificationResult) or not receipt.verified:
            raise ValueError("trusted receipt verification is required")
        if not isinstance(receipt.content_hash, str) or not receipt.content_hash.strip():
            raise ValueError("trusted receipt content hash is required")
        if execution.source_decision_id != outcome.decision_id:
            raise ValueError("execution source_decision_id does not match the outcome")
        if receipt.execution_id != loop.execution_id:
            raise ValueError("trusted receipt execution_id does not match the trace")
        if (
            not isinstance(admission.receipt_content_hash, str)
            or admission.receipt_content_hash != receipt.content_hash
        ):
            raise ValueError("admission receipt hash does not match trusted receipt")
        if not receipt.provider_name.strip() or not receipt.source_record_id.strip():
            raise ValueError("trusted receipt provider and source record are required")
        if not receipt.raw_observation.strip() or not receipt.verification_method.strip():
            raise ValueError("trusted receipt observation and verification method are required")

        return cls(
            decision_id=outcome.decision_id,
            command_id=outcome.command_id,
            execution_id=loop.execution_id,
            trace_id=loop.trace_id,
            evidence_id=evidence_id.strip(),
            policy_version=policy_version.strip(),
            provider_name=receipt.provider_name,
            source_record_id=receipt.source_record_id,
            verification_method=receipt.verification_method,
            receipt_content_hash=receipt.content_hash,
            admission_reasons=admission.reasons,
        )
