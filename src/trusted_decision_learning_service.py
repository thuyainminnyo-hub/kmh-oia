"""Trusted runtime-to-learning application service.

The service re-verifies the receipt through its configured verifier immediately
before learning admission. ExecutionRecord and verifier-result dataclasses are
application contracts, not unforgeable security capabilities; the verifier is
therefore the trust source rather than a caller-supplied result object's type.
"""
from dataclasses import dataclass
from typing import Protocol

from src.adaptation_engine import AdaptationEngine, AdaptationProposal
from src.decision_outcome_evaluator import DecisionOutcome
from src.decision_queue import DecisionItem
from src.evidence_admission_gate import EvidenceAdmissionResult
from src.live_runtime_bridge import ExecutionRecord
from src.operating_memory import OperatingMemory, OperatingMemoryRecord
from src.trusted_source_receipt import (
    ReceiptVerificationResult,
    TrustedSourceReceiptVerifier,
)
from src.verified_learning_admission import VerifiedLearningAdmission


@dataclass(frozen=True)
class TrustedOutcomeClassification:
    """Provider-specific semantic classification derived from a verified receipt."""

    outcome_positive: bool
    reason: str
    evidence_id: str


class TrustedOutcomeClassifier(Protocol):
    """Application-wired adapter that interprets an authenticated provider receipt."""

    def classify(
        self,
        decision: DecisionItem,
        execution: ExecutionRecord,
        receipt: ReceiptVerificationResult,
    ) -> TrustedOutcomeClassification: ...


@dataclass(frozen=True)
class TrustedDecisionLearningResult:
    admitted: bool
    decision_id: str
    command_id: str
    execution_id: str | None
    admission: VerifiedLearningAdmission | None
    outcome: DecisionOutcome | None
    memory: OperatingMemoryRecord | None
    adaptation: AdaptationProposal | None
    reasons: tuple[str, ...]


class TrustedDecisionLearningService:
    """Re-verify runtime receipt evidence before admitting outcome-linked learning."""

    def __init__(
        self,
        *,
        classifier: TrustedOutcomeClassifier | None,
        receipt_verifier: TrustedSourceReceiptVerifier | None,
        memory: OperatingMemory,
        adaptation_engine: AdaptationEngine | None = None,
    ) -> None:
        self._classifier = classifier
        self._receipt_verifier = receipt_verifier
        self._memory = memory
        self._adaptation_engine = adaptation_engine or AdaptationEngine()

    def capture_execution(
        self,
        decision: DecisionItem,
        execution: ExecutionRecord,
        *,
        evidence_id: str,
        policy_version: str,
        next_command: str,
        confidence: float = 1.0,
    ) -> TrustedDecisionLearningResult:
        """Re-verify receipt, re-check attribution, then create a governed candidate.

        Any rejected/incomplete chain fails closed and does not write memory.
        """
        execution_id = (
            execution.operating_loop.execution_id
            if execution.operating_loop is not None else None
        )
        base = dict(
            admitted=False,
            decision_id=decision.id,
            command_id=execution.command_id,
            execution_id=execution_id,
            admission=None,
            outcome=None,
            memory=None,
            adaptation=None,
        )

        def blocked(reason: str, admission=None):
            payload = dict(base)
            payload["admission"] = admission
            return TrustedDecisionLearningResult(**payload, reasons=(reason,))

        if decision.status != "APPROVED":
            return blocked("Decision is not approved.")
        if execution.source_decision_id != decision.id:
            return blocked("Execution source_decision_id does not match the approved decision.")
        if execution.final_status != "LEARNED":
            return blocked("Execution has not reached the LEARNED state.")
        if execution.qa_status != "PASS":
            return blocked("Internal runtime QA did not pass.")
        loop = execution.operating_loop
        if loop is None:
            return blocked("Operating-loop trace is required.")
        if (
            loop.decision_id != decision.id
            or loop.source_decision_id != decision.id
            or loop.command_id != execution.command_id
            or not loop.execution_id.strip()
            or not loop.trace_id.strip()
        ):
            return blocked("Decision/command/execution/trace attribution mismatch.")
        gate = execution.admission
        if not isinstance(gate, EvidenceAdmissionResult):
            return blocked("Runtime evidence admission result is missing.")
        if (
            gate.decision != "ADMITTED"
            or not gate.learning_admitted
            or gate.evidence_status != "OUTCOME_LINKED"
            or loop.learning_status != "ADMITTED"
            or loop.evidence_status != "OUTCOME_LINKED"
        ):
            return blocked("Runtime evidence was not admitted as OUTCOME_LINKED.")
        if self._receipt_verifier is None:
            return blocked("Independent trusted receipt verifier is not configured.")
        recorded_receipt = execution.trusted_receipt_verification
        if not isinstance(recorded_receipt, ReceiptVerificationResult):
            return blocked("Runtime receipt verification result is missing.")
        if not recorded_receipt.verified:
            return blocked("Runtime receipt verification was rejected.")
        if (
            recorded_receipt.execution_id != loop.execution_id
            or not recorded_receipt.content_hash.strip()
            or not recorded_receipt.source_record_id.strip()
            or not recorded_receipt.provider_name.strip()
        ):
            return blocked("Runtime receipt is not attributed to the execution trace.")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            return blocked("evidence_id is required.")
        if not isinstance(policy_version, str) or not policy_version.strip():
            return blocked("policy_version is required.")
        if not isinstance(next_command, str) or not next_command.strip():
            return blocked("next_command is required.")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0.0 <= confidence <= 1.0:
            return blocked("confidence must be between 0 and 1.")
        if self._classifier is None:
            return blocked("Trusted provider outcome classifier is not configured.")

        # Re-fetch and re-authenticate the provider receipt at the learning
        # boundary. A consumed/replayed receipt fails closed in the replay store.
        try:
            receipt = self._receipt_verifier.verify(
                recorded_receipt.source_record_id,
                loop.execution_id,
                claim_replay=False,
            )
        except Exception as exc:
            return blocked(f"Independent receipt verification failed closed ({type(exc).__name__}).")
        if not isinstance(receipt, ReceiptVerificationResult) or not receipt.verified:
            return blocked("Independent receipt verification failed or receipt was replayed.")
        if (
            receipt.provider_name != recorded_receipt.provider_name
            or receipt.source_record_id != recorded_receipt.source_record_id
            or receipt.execution_id != loop.execution_id
            or receipt.raw_observation != recorded_receipt.raw_observation
            or receipt.verification_method != recorded_receipt.verification_method
            or receipt.content_hash != recorded_receipt.content_hash
        ):
            return blocked("Independently verified receipt does not match runtime receipt.")

        expected_source = f"{receipt.provider_name}:{receipt.source_record_id}"
        actual_raw = receipt.raw_observation
        # The verifier provides authoritative attribution; ensure the recorded
        # gate result includes that same source and observation.
        if execution.trusted_receipt_verification.raw_observation != actual_raw:
            return blocked("Runtime raw observation differs from independent receipt.")
        if not expected_source:
            return blocked("Trusted source attribution is incomplete.")

        placeholder = DecisionOutcome(
            decision_id=decision.id,
            command_id=execution.command_id,
            outcome_positive=False,
            quality="NEUTRAL",
            reason="Placeholder used only for identity and admission checks.",
        )
        try:
            admission = VerifiedLearningAdmission.from_execution(
                placeholder,
                execution,
                evidence_id=evidence_id,
                policy_version=policy_version,
            )
        except (AttributeError, TypeError, ValueError) as exc:
            return blocked(f"Learning admission blocked ({type(exc).__name__}).")

        try:
            classification = self._classifier.classify(decision, execution, receipt)
        except Exception as exc:
            return blocked(
                f"Trusted outcome classification failed closed ({type(exc).__name__}).",
                admission,
            )
        if not isinstance(classification, TrustedOutcomeClassification):
            return blocked("Classifier returned an unsupported result contract.", admission)
        if not isinstance(classification.outcome_positive, bool):
            return blocked("Classifier outcome must be a boolean.", admission)
        if not isinstance(classification.reason, str) or not classification.reason.strip():
            return blocked("Classifier reason is required.", admission)
        if (
            not isinstance(classification.evidence_id, str)
            or classification.evidence_id.strip() != evidence_id.strip()
        ):
            return blocked("Classifier evidence_id does not match the admitted evidence.", admission)

        quality = "GOOD" if classification.outcome_positive else "POOR"
        reason = classification.reason.strip()
        outcome = DecisionOutcome(
            decision_id=decision.id,
            command_id=execution.command_id,
            outcome_positive=classification.outcome_positive,
            quality=quality,
            reason=reason,
        )
        memory = self._memory.record(
            command_id=execution.command_id,
            wanted=decision.recommended_action,
            did=execution.response or "Runtime execution completed.",
            actual=receipt.raw_observation,
            verified=(
                f"Receipt independently verified by {receipt.provider_name} using "
                f"{receipt.verification_method}; evidence admitted under "
                f"{policy_version.strip()}."
            ),
            decision=f"Decision {decision.id}: {quality}",
            learned=f"Trusted outcome classification admitted: {reason}",
            changed=(
                "Create a governed adaptation proposal for review."
                if quality == "POOR"
                else "Retain the current rule; no adaptation proposal is required."
            ),
            next_command=next_command.strip(),
            confidence=float(confidence),
        )
        adaptation = None
        if quality == "POOR":
            adaptation = self._adaptation_engine.propose(
                memory,
                pattern=f"decision:{decision.id}",
                problem=reason,
                proposed_change=f"Review the decision rule for {decision.signal_kind}.",
                expected_effect=f"Improve the {decision.signal_kind} outcome under existing guardrails.",
                next_experiment=next_command.strip(),
            )
        return TrustedDecisionLearningResult(
            admitted=True,
            decision_id=decision.id,
            command_id=execution.command_id,
            execution_id=admission.execution_id,
            admission=admission,
            outcome=outcome,
            memory=memory,
            adaptation=adaptation,
            reasons=("Independent receipt verification, attribution, evidence admission, and outcome classification passed.",),
        )
