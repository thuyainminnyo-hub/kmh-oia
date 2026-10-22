"""Trusted runtime-to-learning application service.

The service re-verifies the receipt through its configured verifier immediately
before learning admission. ExecutionRecord and verifier-result dataclasses are
application contracts, not unforgeable security capabilities; the verifier is
therefore the trust source rather than a caller-supplied result object's type.
"""
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Protocol
import hashlib
import json

from src.adaptation_engine import AdaptationEngine, AdaptationProposal
from src.decision_outcome_evaluator import DecisionOutcome
from src.decision_queue import DecisionItem
from src.evidence_admission_gate import EvidenceAdmissionResult
from src.live_runtime_bridge import ExecutionRecord
from src.learning_admission_repository import AdmissionConflictError, SQLiteLearningAdmissionRepository
from src.operating_memory import OperatingMemory, OperatingMemoryRecord
from src.trusted_source_receipt import (
    ReceiptVerificationResult,
    TrustedSourceReceiptVerifier,
)
from src.verified_learning_admission import VerifiedLearningAdmission
from src.runtime_artifact_attestation import RuntimeArtifactAttestation, RuntimeArtifactAttestationVerifier
from src.runtime_artifact_loader import VerifiedRuntimeArtifacts


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
        repository: SQLiteLearningAdmissionRepository,
        adaptation_engine: AdaptationEngine | None = None,
        classifier_artifact_sha256: str | None = None,
        policy_artifact_sha256: str | None = None,
        artifact_attestation: RuntimeArtifactAttestation | None = None,
        artifact_attestation_verifier: RuntimeArtifactAttestationVerifier | None = None,
        runtime_artifacts: VerifiedRuntimeArtifacts | None = None,
    ) -> None:
        self._runtime_artifacts = runtime_artifacts
        if runtime_artifacts is not None:
            # Use identities derived from the verified byte bundle, never caller-only digest strings.
            classifier = runtime_artifacts.classifier
            classifier_artifact_sha256 = runtime_artifacts.classifier_sha256
            policy_artifact_sha256 = runtime_artifacts.policy_sha256
            artifact_attestation = runtime_artifacts.attestation
            artifact_attestation_verifier = runtime_artifacts.verifier
        self._classifier = classifier
        self._classifier_artifact_sha256 = self._normalize_artifact_digest(classifier_artifact_sha256)
        self._policy_artifact_sha256 = self._normalize_artifact_digest(policy_artifact_sha256)
        self._artifact_attestation = artifact_attestation
        self._artifact_attestation_verifier = artifact_attestation_verifier
        self._receipt_verifier = receipt_verifier
        # Kept as a read-side dependency; transactional repository owns writes.
        self._memory = memory
        self._repository = repository
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
        if self._classifier_artifact_sha256 is None:
            return blocked("Immutable classifier artifact SHA-256 is not configured.")
        if self._policy_artifact_sha256 is None:
            return blocked("Immutable policy artifact SHA-256 is not configured.")
        if self._artifact_attestation is None:
            return blocked("Runtime artifact attestation is not configured.")
        if self._artifact_attestation_verifier is None:
            return blocked("Trusted runtime artifact attestation verifier is not configured.")
        attestation = self._artifact_attestation
        if (
            not isinstance(attestation, RuntimeArtifactAttestation)
            or not isinstance(attestation.issuer, str) or not attestation.issuer.strip()
            or not isinstance(attestation.subject, str) or not attestation.subject.strip()
            or not isinstance(attestation.attestation_id, str) or not attestation.attestation_id.strip()
            or self._normalize_artifact_digest(attestation.classifier_sha256) != self._classifier_artifact_sha256
            or self._normalize_artifact_digest(attestation.policy_sha256) != self._policy_artifact_sha256
        ):
            return blocked("Runtime artifact attestation identity is invalid or mismatched.")
        try:
            attestation_valid = self._artifact_attestation_verifier.verify(
                attestation, expected_classifier_sha256=self._classifier_artifact_sha256,
                expected_policy_sha256=self._policy_artifact_sha256,
            )
        except Exception:
            attestation_valid = False
        if attestation_valid is not True:
            return blocked("Runtime artifact attestation verification failed closed.")
        if self._runtime_artifacts is None:
            return blocked("Verified runtime artifact loader bundle is not configured.")
        if self._runtime_artifacts.classifier is not self._classifier:
            return blocked("Loaded classifier object does not match the verified artifact bundle.")
        if (
            self._runtime_artifacts.attestation != self._artifact_attestation
            or self._runtime_artifacts.verifier is not self._artifact_attestation_verifier
            or self._runtime_artifacts.classifier_sha256 != self._classifier_artifact_sha256
            or self._runtime_artifacts.policy_sha256 != self._policy_artifact_sha256
            or self._runtime_artifacts.verify_integrity() is not True
        ):
            return blocked("Verified runtime artifact bundle integrity or provenance validation failed.")

        # Re-fetch and re-authenticate the provider receipt at the learning
        # boundary. A consumed/replayed receipt fails closed in the replay store.
        try:
            receipt = self._receipt_verifier.verify(
                recorded_receipt.source_record_id,
                loop.execution_id,
                claim_replay=False,
            )
        except Exception:
            return blocked("Independent receipt verification failed closed.")
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

        try:
            admission_key, fingerprint = self._admission_identity(
                decision, execution, receipt, evidence_id=evidence_id,
                policy_version=policy_version, next_command=next_command,
                confidence=float(confidence),
            )
        except (TypeError, ValueError):
            return blocked("Artifact identity or admission request is invalid.")
        try:
            stored = self._repository.get(admission_key)
        except Exception:
            return blocked("Transactional admission store is unavailable; learning was not admitted.")
        if stored is not None:
            if stored.fingerprint != fingerprint:
                return blocked("Admission identity was reused with different verified request content.")
            try:
                return self._restore_result(stored.result)
            except Exception:
                return blocked("Persisted admission result could not be restored safely.")

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
        except (AttributeError, TypeError, ValueError):
            return blocked("Learning admission blocked by invalid execution evidence.")

        try:
            classification = self._classifier.classify(decision, execution, receipt)
        except Exception:
            return blocked(
                "Trusted outcome classification failed closed.",
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
        try:
            fields = {
                "wanted": decision.recommended_action,
                "did": execution.response or "Runtime execution completed.",
                "actual": receipt.raw_observation,
                "verified": f"Receipt independently verified by {receipt.provider_name} using {receipt.verification_method}; evidence admitted under {policy_version.strip()}.",
                "decision": f"Decision {decision.id}: {quality}",
                "learned": f"Trusted outcome classification admitted: {reason}",
                "changed": "Create a governed adaptation proposal for review." if quality == "POOR" else "Retain the current rule; no adaptation proposal is required.",
                "next_command": next_command.strip(),
            }
            for name, value in fields.items():
                if not isinstance(value, str) or not value.strip():
                    return blocked(f"Learning record field {name} is missing or invalid.", admission)
            memory = OperatingMemoryRecord(
                command_id=execution.command_id.strip(), timestamp=datetime.now(timezone.utc).isoformat(),
                **{name: value.strip() for name, value in fields.items()}, confidence=float(confidence),
            )
            adaptation = None
            if quality == "POOR":
                adaptation = self._adaptation_engine.propose(
                    memory, pattern=f"decision:{decision.id}", problem=reason,
                    proposed_change=f"Review the decision rule for {decision.signal_kind}.",
                    expected_effect=f"Improve the {decision.signal_kind} outcome under existing guardrails.",
                    next_experiment=next_command.strip(),
                )
                adaptation = replace(adaptation, id=f"adapt:{admission_key.removeprefix('learning:')}", status="PROPOSED")
        except Exception:
            return blocked("Learning payload construction failed closed.", admission)

        pending_result = TrustedDecisionLearningResult(
            admitted=True, decision_id=decision.id, command_id=execution.command_id,
            execution_id=admission.execution_id, admission=admission, outcome=outcome,
            memory=memory, adaptation=adaptation,
            reasons=("Independent receipt verification, attribution, evidence admission, and outcome classification passed.",),
        )
        key_digest = hashlib.sha256(admission_key.encode("utf-8")).hexdigest()
        audit = {
            "event_id": f"audit:{key_digest}", "admission_key": admission_key,
            "kind": "TRUSTED_LEARNING_ADMITTED", "decision_id": decision.id,
            "command_id": execution.command_id, "execution_id": admission.execution_id,
            "trace_id": admission.trace_id, "evidence_id": admission.evidence_id,
            "policy_version": admission.policy_version, "provider_name": receipt.provider_name,
            "source_record_id": receipt.source_record_id, "content_hash": receipt.content_hash,
            "classifier_artifact_sha256": self._classifier_artifact_sha256,
            "policy_artifact_sha256": self._policy_artifact_sha256,
            "artifact_attestation_issuer": self._artifact_attestation.issuer,
            "artifact_attestation_subject": self._artifact_attestation.subject,
            "artifact_attestation_id": self._artifact_attestation.attestation_id,
            "artifact_attestation_key_id": self._artifact_attestation.key_id or None,
            "artifact_attestation_source_revision": self._artifact_attestation.source_revision or None,
            "artifact_attestation_build_run_id": self._artifact_attestation.build_run_id or None,
            "artifact_attestation_issued_at": self._artifact_attestation.issued_at or None,
            "artifact_attestation_signature_sha256": (
                hashlib.sha256(self._artifact_attestation.signature.encode("utf-8")).hexdigest()
                if self._artifact_attestation.signature else None
            ),
            "outcome_quality": quality,
        }
        try:
            committed = self._repository.commit(
                admission_key=admission_key, fingerprint=fingerprint,
                learning_record=asdict(memory),
                adaptation_proposal=asdict(adaptation) if adaptation is not None else None,
                audit_event=audit, result=asdict(pending_result),
            )
            return self._restore_result(committed.result)
        except AdmissionConflictError:
            return blocked("Admission identity was concurrently reused with different request content.", admission)
        except Exception:
            return blocked("Transactional learning persistence failed; admission was not confirmed.", admission)

    def _admission_identity(
        self, decision: DecisionItem, execution: ExecutionRecord,
        receipt: ReceiptVerificationResult, *, evidence_id: str,
        policy_version: str, next_command: str, confidence: float,
    ) -> tuple[str, str]:
        loop, gate = execution.operating_loop, execution.admission
        identity = {"decision_id": decision.id, "execution_id": loop.execution_id, "evidence_id": evidence_id.strip()}
        admission_key = "learning:" + hashlib.sha256(json.dumps(
            identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")).hexdigest()
        classifier_type = type(self._classifier)
        classifier = f"{classifier_type.__module__}.{classifier_type.__qualname__}"
        classifier_version = getattr(self._classifier, "version", None)
        if isinstance(classifier_version, str) and classifier_version.strip():
            classifier = f"{classifier}@{classifier_version.strip()}"
        # A class name/version is useful metadata, but it is not proof of the
        # artifact bytes. These externally verified immutable digests are part
        # of the canonical request fingerprint and audit trail.
        if self._classifier_artifact_sha256 is None or self._policy_artifact_sha256 is None:
            raise ValueError("immutable classifier and policy artifact digests are required")
        request = {
            "schema": "trusted-learning-admission-v1", "identity": identity,
            "decision": asdict(decision),
            "execution": {"command_id": execution.command_id, "response": execution.response,
                "final_status": execution.final_status, "qa_status": execution.qa_status,
                "source_decision_id": execution.source_decision_id,
                "operating_loop": asdict(loop), "admission": asdict(gate)},
            "receipt": {"provider_name": receipt.provider_name, "source_record_id": receipt.source_record_id,
                "execution_id": receipt.execution_id, "raw_observation": receipt.raw_observation,
                "verification_method": receipt.verification_method, "content_hash": receipt.content_hash},
            "policy_version": policy_version.strip(), "next_command": next_command.strip(),
            "confidence": confidence, "classifier": classifier,
            "classifier_artifact_sha256": self._classifier_artifact_sha256,
            "policy_artifact_sha256": self._policy_artifact_sha256,
            "attestation_issuer": self._artifact_attestation.issuer if self._artifact_attestation else None,
            "attestation_subject": self._artifact_attestation.subject if self._artifact_attestation else None,
            "attestation_id": self._artifact_attestation.attestation_id if self._artifact_attestation else None,
            "attestation_key_id": self._artifact_attestation.key_id if self._artifact_attestation else None,
            "attestation_source_revision": self._artifact_attestation.source_revision if self._artifact_attestation else None,
            "attestation_build_run_id": self._artifact_attestation.build_run_id if self._artifact_attestation else None,
            "attestation_issued_at": self._artifact_attestation.issued_at if self._artifact_attestation else None,
            "attestation_signature_sha256": (
                hashlib.sha256(self._artifact_attestation.signature.encode("utf-8")).hexdigest()
                if self._artifact_attestation and self._artifact_attestation.signature else None
            ),
        }
        fingerprint = "sha256:" + hashlib.sha256(json.dumps(
            request, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")).hexdigest()
        return admission_key, fingerprint

    @staticmethod
    def _normalize_artifact_digest(value: str | None) -> str | None:
        """Accept only a bare or sha256:-prefixed, 64-hex SHA-256 digest."""
        if not isinstance(value, str):
            return None
        candidate = value.strip()
        if candidate.startswith("sha256:"):
            candidate = candidate[7:]
        if len(candidate) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in candidate):
            return None
        return candidate.lower()

    @staticmethod
    def _restore_result(payload: dict) -> TrustedDecisionLearningResult:
        if not isinstance(payload, dict):
            raise TypeError("persisted result must be an object")
        admission_payload = payload.get("admission")
        admission = None
        if admission_payload is not None:
            admission_payload = dict(admission_payload)
            admission_payload["admission_reasons"] = tuple(admission_payload["admission_reasons"])
            admission = VerifiedLearningAdmission(**admission_payload)
        outcome_payload, memory_payload, adaptation_payload = payload.get("outcome"), payload.get("memory"), payload.get("adaptation")
        return TrustedDecisionLearningResult(
            admitted=bool(payload["admitted"]), decision_id=payload["decision_id"],
            command_id=payload["command_id"], execution_id=payload.get("execution_id"),
            admission=admission,
            outcome=DecisionOutcome(**outcome_payload) if outcome_payload is not None else None,
            memory=OperatingMemoryRecord(**memory_payload) if memory_payload is not None else None,
            adaptation=AdaptationProposal(**adaptation_payload) if adaptation_payload is not None else None,
            reasons=tuple(payload["reasons"]),
        )
