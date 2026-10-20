"""Trusted runtime-to-learning application service.

This service is the only supported application path for admitting decision
outcomes into learning. The provider-specific outcome classifier must be
configured by trusted application wiring; caller-supplied outcome booleans are
never accepted here. Python objects are application contracts, not a security
boundary against arbitrary code executing in the same process.
"""
from dataclasses import dataclass
from typing import Protocol

from src.adaptation_engine import AdaptationEngine, AdaptationProposal
from src.decision_outcome_evaluator import DecisionOutcome
from src.decision_queue import DecisionItem
from src.evidence_admission_gate import EvidenceAdmissionResult
from src.live_runtime_bridge import ExecutionRecord
from src.operating_memory import OperatingMemory, OperatingMemoryRecord
from src.trusted_source_receipt import ReceiptVerificationResult
from src.verified_learning_admission import VerifiedLearningAdmission


@dataclass(frozen=True)
class TrustedOutcomeClassification:
    """Provider-specific semantic classification derived from verified receipt data."""

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
    """Admit only runtime-linked, receipt-verified outcomes into governed learning."""

    def __init__(
        self,
        *,
        classifier: TrustedOutcomeClassifier | None,
        memory: OperatingMemory,
        adaptation_engine: AdaptationEngine | None = None,
    ) -> None:
        self._classifier = classifier
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
        """Validate trusted runtime evidence, classify it, then create a governed candidate.

        A rejected or incomplete chain returns a non-admitted result and does not
        write to operating memory or create an adaptation proposal.
        """
        base = dict(
            admitted=False,
            decision_id=decision.id,
            command_id=execution.command_id,
            execution_id=(
                execution.operating_loop.execution_id
                if execution.operating_loop is not None else None
            ),
            admission=None,
            outcome=None,
            memory=None,
            adaptation=None,
        )
        if decision.status != "APPROVED":
            return TrustedDecisionLearningResult(
                **base, reasons=("Decision is not approved.",)
            )
        if self._classifier is None:
            return TrustedDecisionLearningResult(
                **base, reasons=("Trusted provider outcome classifier is not configured.",)
            )
        if not isinstance(execution.admission, EvidenceAdmissionResult):
            return TrustedDecisionLearningResult(
                **base, reasons=("Runtime evidence admission result is missing.",)
            )
        receipt = execution.trusted_receipt_verification
        if not isinstance(receipt, ReceiptVerificationResult) or not receipt.verified:
            return TrustedDecisionLearningResult(
                **base, reasons=("Trusted receipt verification is missing or rejected.",)
            )
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            return TrustedDecisionLearningResult(
                **base, reasons=("evidence_id is required.",)
            )
        if not isinstance(policy_version, str) or not policy_version.strip():
            return TrustedDecisionLearningResult(
                **base, reasons=("policy_version is required.",)
            )
        if not isinstance(next_command, str) or not next_command.strip():
            return TrustedDecisionLearningResult(
                **base, reasons=("next_command is required.",)
            )

        # Use a neutral placeholder only to validate the execution-to-decision
        # attribution before any provider-specific outcome classification.
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
            return TrustedDecisionLearningResult(
                **base, reasons=(f"Learning admission blocked ({type(exc).__name__}).",)
            )

        try:
            classification = self._classifier.classify(decision, execution, receipt)
        except Exception as exc:
            return TrustedDecisionLearningResult(
                **base,
                admission=admission,
                reasons=(f"Trusted outcome classification failed closed ({type(exc).__name__}).",),
            )
        if not isinstance(classification, TrustedOutcomeClassification):
            return TrustedDecisionLearningResult(
                **base,
                admission=admission,
                reasons=("Classifier returned an unsupported result contract.",),
            )
        if not isinstance(classification.outcome_positive, bool):
            return TrustedDecisionLearningResult(
                **base,
                admission=admission,
                reasons=("Classifier outcome must be a boolean.",),
            )
        if not classification.reason.strip():
            return TrustedDecisionLearningResult(
                **base,
                admission=admission,
                reasons=("Classifier reason is required.",),
            )
        if classification.evidence_id.strip() != evidence_id.strip():
            return TrustedDecisionLearningResult(
                **base,
                admission=admission,
                reasons=("Classifier evidence_id does not match the admitted evidence.",),
            )

        quality = "GOOD" if classification.outcome_positive else "POOR"
        outcome = DecisionOutcome(
            decision_id=decision.id,
            command_id=execution.command_id,
            outcome_positive=classification.outcome_positive,
            quality=quality,
            reason=classification.reason.strip(),
        )
        memory = self._memory.record(
            command_id=execution.command_id,
            wanted=decision.recommended_action,
            did=execution.response,
            actual=receipt.raw_observation,
            verified=(
                f"Receipt verified by {receipt.provider_name} using "
                f"{receipt.verification_method}; evidence admitted under "
                f"{policy_version.strip()}."
            ),
            decision=f"Decision {decision.id}: {quality}",
            learned=(
                f"Trusted outcome classification admitted: {classification.reason.strip()}"
            ),
            changed=(
                "Create a governed adaptation proposal for review."
                if quality == "POOR"
                else "Retain the current rule; no adaptation proposal is required."
            ),
            next_command=next_command.strip(),
            confidence=confidence,
        )
        adaptation = None
        if quality == "POOR":
            adaptation = self._adaptation_engine.propose(
                memory,
                pattern=f"decision:{decision.id}",
                problem=classification.reason.strip(),
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
            reasons=("Trusted receipt, attribution, admission, and outcome classification passed.",),
        )
