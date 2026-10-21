import hashlib
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone

from src.decision_queue import DecisionItem
from src.evidence_admission_gate import EvidenceAdmissionResult
from src.live_runtime_bridge import ExecutionRecord
from src.operating_loop_record import OperatingLoopRecord
from src.operating_memory import OperatingMemory
from src.learning_admission_repository import SQLiteLearningAdmissionRepository
from src.trusted_decision_learning_service import (
    RuntimeArtifactAttestation,
    TrustedDecisionLearningService,
    TrustedOutcomeClassification,
)
from src.runtime_artifact_loader import verify_and_load_runtime_artifacts_from_bytes
from src.trusted_source_receipt import (
    ReceiptVerificationResult,
    TrustedSourceReceipt,
    TrustedSourceReceiptVerifier,
)


class FakeTrustedSourceAdapter:
    provider_name = "booking-provider"

    def __init__(self):
        self.calls = 0

    def fetch_receipt(self, source_record_id, execution_id):
        self.calls += 1
        return TrustedSourceReceipt(
            provider_name=self.provider_name,
            source_record_id=source_record_id,
            execution_id=execution_id,
            raw_observation="booking outcome=failed",
            observed_at=datetime.now(timezone.utc).isoformat(),
            content_hash="sha256:receipt-stable",
            verification_method="test-provider-signature-and-attribution",
        )

    def verify_receipt(self, receipt):
        return receipt.content_hash.startswith("sha256:")

    def match_execution(self, receipt, execution_id):
        return receipt.execution_id == execution_id


class FakeArtifactAttestationVerifier:
    def __init__(self, valid=True):
        self.valid = valid
        self.calls = 0

    def verify(self, attestation, *, expected_classifier_sha256, expected_policy_sha256):
        self.calls += 1
        return self.valid and attestation.classifier_sha256 == expected_classifier_sha256 and attestation.policy_sha256 == expected_policy_sha256


TEST_CLASSIFIER_BYTES = b"test-classifier-runtime-blob-phase805"
TEST_POLICY_BYTES = b"test-policy-runtime-blob-phase805"


def make_runtime_artifacts(classifier, *, classifier_bytes=TEST_CLASSIFIER_BYTES, policy_bytes=TEST_POLICY_BYTES):
    classifier_digest = hashlib.sha256(classifier_bytes).hexdigest()
    policy_digest = hashlib.sha256(policy_bytes).hexdigest()
    attestation = RuntimeArtifactAttestation(
        classifier_sha256=classifier_digest, policy_sha256=policy_digest,
        issuer="test-ci", subject="test-loaded-runtime",
        attestation_id="attestation:phase-805-test",
    )
    verifier = FakeArtifactAttestationVerifier()
    return verify_and_load_runtime_artifacts_from_bytes(
        classifier_bytes, policy_bytes, attestation=attestation, verifier=verifier,
        classifier_loader=lambda payload: classifier if payload == classifier_bytes else None,
        policy_loader=lambda payload: {"policy_bytes_sha256": hashlib.sha256(payload).hexdigest()} if payload == policy_bytes else None,
    )

class TestClassifier:
    def __init__(self, result=None, error=None):
        self.result = result or TrustedOutcomeClassification(
            outcome_positive=False,
            reason="Provider receipt reports a failed booking outcome.",
            evidence_id="evidence:1",
        )
        self.error = error
        self.calls = 0

    def classify(self, decision, execution, receipt):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class TrustedDecisionLearningServiceTests(unittest.TestCase):
    def setUp(self):
        self.decision = DecisionItem(
            id="decision:1", signal_kind="QUALITY_RISK", severity="HIGH",
            problem="Quality issue", recommended_action="Review quality",
            owner="system", status="APPROVED",
        )
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.memory = OperatingMemory()
        self.repository = SQLiteLearningAdmissionRepository(Path(self.tempdir.name) / "learning.sqlite3")
        self.classifier = TestClassifier()
        self.adapter = FakeTrustedSourceAdapter()
        self.verifier = TrustedSourceReceiptVerifier(
            self.adapter,
            allowed_providers=("booking-provider",),
        )
        self.runtime_artifacts = make_runtime_artifacts(self.classifier)
        self.attestation = self.runtime_artifacts.attestation
        self.attestation_verifier = self.runtime_artifacts.verifier
        self.service = TrustedDecisionLearningService(
            classifier=self.classifier,
            receipt_verifier=self.verifier,
            memory=self.memory,
            repository=self.repository,
            classifier_artifact_sha256="a" * 64,
            policy_artifact_sha256="b" * 64,
            artifact_attestation=self.attestation,
            artifact_attestation_verifier=self.attestation_verifier,
            runtime_artifacts=self.runtime_artifacts,
        )

    def execution(self, *, admitted=True, receipt=True, decision_id="decision:1",
                  command_id="cmd:1", final_status="LEARNED",
                  receipt_result=None):
        loop = OperatingLoopRecord(
            context_id="context:1", decision_id=decision_id, command_id=command_id,
            execution_id="exec:1", trace_id="trace:1", qa_status="PASS",
            evidence_status="OUTCOME_LINKED" if admitted else "OBSERVED",
            learning_status="ADMITTED" if admitted else "NOT_ADMITTED",
            source_decision_id=decision_id,
        )
        gate = EvidenceAdmissionResult(
            decision="ADMITTED" if admitted else "NOT_ADMITTED",
            evidence_status="OUTCOME_LINKED" if admitted else "OBSERVED",
            learning_admitted=admitted,
            missing_fields=() if admitted else ("trusted_receipt_verification",),
            reasons=("test admission result",),
            execution_id="exec:1",
            source="booking-provider:record:1",
            raw_observation="booking outcome=failed",
            trusted_receipt_content_hash="sha256:receipt-stable",
        )
        result = receipt_result
        if receipt and result is None:
            result = ReceiptVerificationResult(
                verified=True, provider_name="booking-provider",
                source_record_id="record:1", execution_id="exec:1",
                raw_observation="booking outcome=failed",
                verification_method="test-provider-signature-and-attribution",
                reasons=("test receipt",), content_hash="sha256:receipt-stable",
            )
        return ExecutionRecord(
            command_id=command_id, response="runtime completed",
            trace_stages=("input_gateway", "evaluation"),
            evidence=("trace_id=trace:1",), qa_status="PASS",
            final_status=final_status, source_decision_id=decision_id,
            operating_loop=loop, admission=gate,
            trusted_receipt_verification=result,
        )

    def capture(self, execution=None, decision=None):
        return self.service.capture_execution(
            decision or self.decision,
            execution or self.execution(),
            evidence_id="evidence:1", policy_version="policy:v1",
            next_command="Run a bounded shadow experiment",
        )

    def test_independent_receipt_verification_creates_proposed_not_applied_adaptation(self):
        result = self.capture()
        self.assertTrue(result.admitted)
        self.assertEqual(result.outcome.quality, "POOR")
        self.assertEqual(result.adaptation.status, "PROPOSED")
        self.assertEqual(self.memory.recent(), ())
        self.assertEqual(self.repository.counts()["learning_records"], 1)
        self.assertEqual(self.adapter.calls, 1)
        with self.assertRaisesRegex(ValueError, "only approved adaptations can be applied"):
            self.service._adaptation_engine.apply(result.adaptation)

    def test_duplicate_capture_returns_stored_result_without_reclassification(self):
        first = self.capture()
        calls_after_first = self.classifier.calls
        second = self.capture()
        self.assertEqual(second, first)
        self.assertEqual(self.classifier.calls, calls_after_first)
        self.assertEqual(self.repository.counts(), {
            "learning_admissions": 1, "learning_records": 1,
            "adaptation_proposals": 1, "admission_audit_events": 1,
        })
        self.assertEqual(self.memory.recent(), ())

    def test_same_admission_identity_with_changed_policy_is_rejected(self):
        first = self.capture()
        self.assertTrue(first.admitted)
        calls_after_first = self.classifier.calls
        conflict = self.service.capture_execution(
            self.decision, self.execution(), evidence_id="evidence:1",
            policy_version="policy:v2", next_command="Run a bounded shadow experiment",
        )
        self.assertFalse(conflict.admitted)
        self.assertIn("different verified request content", conflict.reasons[0])
        self.assertEqual(self.classifier.calls, calls_after_first)
        self.assertEqual(self.repository.counts()["learning_records"], 1)


    def test_admission_fails_closed_without_verified_loader_bundle(self):
        service = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=self.verifier, memory=self.memory,
            repository=self.repository, classifier_artifact_sha256=self.runtime_artifacts.classifier_sha256,
            policy_artifact_sha256=self.runtime_artifacts.policy_sha256,
            artifact_attestation=self.runtime_artifacts.attestation,
            artifact_attestation_verifier=self.runtime_artifacts.verifier,
        )
        result = service.capture_execution(
            self.decision, self.execution(), evidence_id="evidence:1",
            policy_version="policy:v1", next_command="Hold",
        )
        self.assertFalse(result.admitted)
        self.assertIn("Verified runtime artifact loader bundle", result.reasons[0])
        self.assertEqual(self.classifier.calls, 0)

    def test_bundle_bytes_must_match_signed_digests_before_admission(self):
        from dataclasses import replace
        bad_bundle = replace(self.runtime_artifacts, classifier_bytes=b"mutated bytes")
        service = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=self.verifier, memory=self.memory,
            repository=self.repository, runtime_artifacts=bad_bundle,
        )
        result = service.capture_execution(
            self.decision, self.execution(), evidence_id="evidence:1",
            policy_version="policy:v1", next_command="Hold",
        )
        self.assertFalse(result.admitted)
        self.assertIn("bundle integrity", result.reasons[0])
        self.assertEqual(self.classifier.calls, 0)

    def test_loader_is_not_called_when_signature_is_rejected(self):
        from src.runtime_artifact_loader import RuntimeArtifactLoadError, verify_and_load_runtime_artifacts_from_bytes
        calls = {"classifier": 0, "policy": 0}
        rejected = FakeArtifactAttestationVerifier(valid=False)
        with self.assertRaises(RuntimeArtifactLoadError):
            verify_and_load_runtime_artifacts_from_bytes(
                TEST_CLASSIFIER_BYTES, TEST_POLICY_BYTES, attestation=self.attestation, verifier=rejected,
                classifier_loader=lambda payload: calls.__setitem__("classifier", calls["classifier"] + 1),
                policy_loader=lambda payload: calls.__setitem__("policy", calls["policy"] + 1),
            )
        self.assertEqual(calls, {"classifier": 0, "policy": 0})

    def test_missing_runtime_attestation_fails_closed(self):
        service = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=self.verifier, memory=self.memory,
            repository=self.repository, classifier_artifact_sha256="a" * 64, policy_artifact_sha256="b" * 64,
        )
        result = service.capture_execution(self.decision, self.execution(), evidence_id="evidence:1", policy_version="policy:v1", next_command="Hold")
        self.assertFalse(result.admitted)
        self.assertIn("Runtime artifact attestation is not configured", result.reasons[0])
        self.assertEqual(self.classifier.calls, 0)
        self.assertEqual(self.repository.counts()["learning_records"], 0)

    def test_missing_attestation_verifier_fails_closed(self):
        service = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=self.verifier, memory=self.memory, repository=self.repository,
            classifier_artifact_sha256="a" * 64, policy_artifact_sha256="b" * 64, artifact_attestation=self.attestation,
        )
        result = service.capture_execution(self.decision, self.execution(), evidence_id="evidence:1", policy_version="policy:v1", next_command="Hold")
        self.assertFalse(result.admitted)
        self.assertIn("Trusted runtime artifact attestation verifier", result.reasons[0])
        self.assertEqual(self.classifier.calls, 0)

    def test_rejected_attestation_fails_closed(self):
        service = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=self.verifier, memory=self.memory, repository=self.repository,
            classifier_artifact_sha256="a" * 64, policy_artifact_sha256="b" * 64, artifact_attestation=self.attestation,
            artifact_attestation_verifier=FakeArtifactAttestationVerifier(valid=False),
        )
        result = service.capture_execution(self.decision, self.execution(), evidence_id="evidence:1", policy_version="policy:v1", next_command="Hold")
        self.assertFalse(result.admitted)
        self.assertIn("attestation verification failed", result.reasons[0])
        self.assertEqual(self.classifier.calls, 0)

    def test_attestation_digest_mismatch_fails_closed(self):
        mismatch = RuntimeArtifactAttestation(
            classifier_sha256="c" * 64, policy_sha256="b" * 64, issuer="test-ci",
            subject="test-loaded-runtime", attestation_id="attestation:mismatch",
        )
        service = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=self.verifier, memory=self.memory, repository=self.repository,
            classifier_artifact_sha256="a" * 64, policy_artifact_sha256="b" * 64, artifact_attestation=mismatch,
            artifact_attestation_verifier=self.attestation_verifier,
        )
        result = service.capture_execution(self.decision, self.execution(), evidence_id="evidence:1", policy_version="policy:v1", next_command="Hold")
        self.assertFalse(result.admitted)
        self.assertIn("invalid or mismatched", result.reasons[0])
        self.assertEqual(self.classifier.calls, 0)

    def test_missing_immutable_artifact_digests_fail_closed(self):
        service = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=self.verifier,
            memory=self.memory, repository=self.repository,
        )
        result = service.capture_execution(
            self.decision, self.execution(), evidence_id="evidence:1",
            policy_version="policy:v1", next_command="Hold for verification",
        )
        self.assertFalse(result.admitted)
        self.assertIn("Immutable classifier artifact SHA-256", result.reasons[0])
        self.assertEqual(self.classifier.calls, 0)
        self.assertEqual(self.repository.counts()["learning_records"], 0)

    def test_invalid_artifact_digest_fails_closed(self):
        service = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=self.verifier,
            memory=self.memory, repository=self.repository,
            classifier_artifact_sha256="not-a-digest",
            policy_artifact_sha256="b" * 64,
        )
        result = service.capture_execution(
            self.decision, self.execution(), evidence_id="evidence:1",
            policy_version="policy:v1", next_command="Hold for verification",
        )
        self.assertFalse(result.admitted)
        self.assertIn("Immutable classifier artifact SHA-256", result.reasons[0])
        self.assertEqual(self.classifier.calls, 0)

    def test_classifier_artifact_change_conflicts_with_same_admission_identity(self):
        first = self.capture()
        self.assertTrue(first.admitted)
        changed_bundle = make_runtime_artifacts(self.classifier, classifier_bytes=b"different-classifier-runtime-blob", policy_bytes=TEST_POLICY_BYTES)
        changed = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=self.verifier,
            memory=self.memory, repository=self.repository,
            runtime_artifacts=changed_bundle,
        )
        calls = self.classifier.calls
        result = changed.capture_execution(
            self.decision, self.execution(), evidence_id="evidence:1",
            policy_version="policy:v1", next_command="Run a bounded shadow experiment",
        )
        self.assertFalse(result.admitted)
        self.assertIn("different verified request content", result.reasons[0])
        self.assertEqual(self.classifier.calls, calls)
        self.assertEqual(self.repository.counts()["learning_records"], 1)

    def test_policy_artifact_change_conflicts_with_same_admission_identity(self):
        first = self.capture()
        self.assertTrue(first.admitted)
        changed_bundle = make_runtime_artifacts(self.classifier, classifier_bytes=TEST_CLASSIFIER_BYTES, policy_bytes=b"different-policy-runtime-blob")
        changed = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=self.verifier,
            memory=self.memory, repository=self.repository,
            runtime_artifacts=changed_bundle,
        )
        calls = self.classifier.calls
        result = changed.capture_execution(
            self.decision, self.execution(), evidence_id="evidence:1",
            policy_version="policy:v1", next_command="Run a bounded shadow experiment",
        )
        self.assertFalse(result.admitted)
        self.assertIn("different verified request content", result.reasons[0])
        self.assertEqual(self.classifier.calls, calls)
        self.assertEqual(self.repository.counts()["learning_records"], 1)

    def test_same_verified_artifacts_preserve_idempotent_retry(self):
        first = self.capture()
        calls = self.classifier.calls
        second = self.capture()
        self.assertEqual(second, first)
        self.assertEqual(self.classifier.calls, calls)
        self.assertEqual(self.repository.counts()["learning_records"], 1)

    def test_missing_receipt_fails_closed_without_learning_influence(self):
        result = self.capture(execution=self.execution(receipt=False))
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)
        self.assertIsNone(result.adaptation)
        self.assertEqual(self.memory.recent(), ())
        self.assertEqual(self.classifier.calls, 0)
        self.assertEqual(self.adapter.calls, 0)

    def test_unadmitted_evidence_fails_closed_without_classification(self):
        result = self.capture(execution=self.execution(admitted=False))
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)
        self.assertEqual(self.classifier.calls, 0)

    def test_decision_trace_mismatch_fails_closed(self):
        result = self.capture(execution=self.execution(decision_id="other:decision"))
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)

    def test_classifier_evidence_mismatch_fails_closed(self):
        self.classifier.result = TrustedOutcomeClassification(
            outcome_positive=True, reason="Provider reports success",
            evidence_id="other-evidence",
        )
        result = self.capture()
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)
        self.assertIsNone(result.adaptation)

    def test_good_outcome_records_learning_without_proposal(self):
        self.classifier.result = TrustedOutcomeClassification(
            outcome_positive=True,
            reason="Provider receipt confirms the intended outcome.",
            evidence_id="evidence:1",
        )
        result = self.capture()
        self.assertTrue(result.admitted)
        self.assertEqual(result.outcome.quality, "GOOD")
        self.assertIsNone(result.adaptation)

    def test_missing_trusted_classifier_fails_closed(self):
        service = TrustedDecisionLearningService(
            classifier=None, receipt_verifier=self.verifier, memory=self.memory,
            repository=self.repository,
            classifier_artifact_sha256="a" * 64, policy_artifact_sha256="b" * 64,
            artifact_attestation=self.attestation,
            artifact_attestation_verifier=self.attestation_verifier,
        )
        result = service.capture_execution(
            self.decision, self.execution(), evidence_id="evidence:1",
            policy_version="policy:v1", next_command="Hold for verification",
        )
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)
        self.assertEqual(self.memory.recent(), ())

    def test_missing_independent_verifier_fails_closed(self):
        service = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=None, memory=self.memory,
            repository=self.repository,
            classifier_artifact_sha256="a" * 64, policy_artifact_sha256="b" * 64,
            artifact_attestation=self.attestation,
            artifact_attestation_verifier=self.attestation_verifier,
        )
        result = service.capture_execution(
            self.decision, self.execution(), evidence_id="evidence:1",
            policy_version="policy:v1", next_command="Hold for verification",
        )
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)
        self.assertEqual(self.classifier.calls, 0)

    def test_forged_runtime_receipt_is_rejected_by_independent_verifier(self):
        forged = ReceiptVerificationResult(
            verified=True, provider_name="booking-provider",
            source_record_id="record:forged", execution_id="exec:1",
            raw_observation="caller fabricated this", verification_method="fake",
            reasons=("caller claim",),
        )
        result = self.capture(execution=self.execution(receipt_result=forged))
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)
        self.assertIsNone(result.adaptation)
        self.assertEqual(self.classifier.calls, 0)


    def test_changed_content_hash_between_runtime_and_learning_recheck_fails_closed(self):
        class RotatingHashAdapter(FakeTrustedSourceAdapter):
            def __init__(self):
                super().__init__()
                self.fetches = 0

            def fetch_receipt(self, source_record_id, execution_id):
                self.fetches += 1
                receipt = super().fetch_receipt(source_record_id, execution_id)
                return TrustedSourceReceipt(
                    provider_name=receipt.provider_name,
                    source_record_id=receipt.source_record_id,
                    execution_id=receipt.execution_id,
                    raw_observation=receipt.raw_observation,
                    observed_at=receipt.observed_at,
                    content_hash=("sha256:receipt-stable" if self.fetches == 1 else "sha256:receipt-mutated"),
                    verification_method=receipt.verification_method,
                )

        adapter = RotatingHashAdapter()
        verifier = TrustedSourceReceiptVerifier(
            adapter, allowed_providers=("booking-provider",)
        )
        runtime_receipt = verifier.verify("record:1", "exec:1")
        self.assertTrue(runtime_receipt.verified)
        execution = self.execution(receipt_result=runtime_receipt)
        service = TrustedDecisionLearningService(
            classifier=self.classifier, receipt_verifier=verifier, memory=self.memory,
            repository=self.repository,
            artifact_attestation=self.attestation,
            artifact_attestation_verifier=self.attestation_verifier,
            runtime_artifacts=self.runtime_artifacts,
        )
        result = service.capture_execution(
            self.decision, execution, evidence_id="evidence:1",
            policy_version="policy:v1", next_command="Run a bounded shadow experiment",
        )
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)
        self.assertIsNone(result.adaptation)
        self.assertEqual(self.classifier.calls, 0)

    def test_classifier_failure_fails_closed_without_leaking_exception_details(self):
        self.classifier.error = RuntimeError("private classifier API key detail")
        result = self.capture()
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)
        self.assertIsNone(result.adaptation)
        self.assertEqual(self.memory.recent(), ())
        self.assertEqual(
            result.reasons,
            ("Trusted outcome classification failed closed.",),
        )
        self.assertNotIn("RuntimeError", result.reasons[0])
        self.assertNotIn("private classifier API key detail", result.reasons[0])

    def test_rejected_adaptation_cannot_be_applied(self):
        result = self.capture()
        self.assertTrue(result.admitted)
        self.assertIsNotNone(result.adaptation)
        self.assertEqual(result.adaptation.status, "PROPOSED")
        rejected = self.service._adaptation_engine.reject(result.adaptation)
        self.assertEqual(rejected.status, "REJECTED")
        with self.assertRaisesRegex(ValueError, "only approved adaptations can be applied"):
            self.service._adaptation_engine.apply(rejected)
        with self.assertRaisesRegex(ValueError, "only approved adaptations can be applied"):
            self.service._adaptation_engine.apply(result.adaptation)
        self.assertEqual(self.memory.recent(), ())
        self.assertEqual(self.repository.counts()["learning_records"], 1)

    def test_independent_verifier_failure_fails_closed_without_leaking_exception_details(self):
        class RaisingVerifier:
            def verify(self, source_record_id, execution_id, *, claim_replay=True):
                raise RuntimeError("private verifier endpoint/token detail")

        service = TrustedDecisionLearningService(
            classifier=self.classifier,
            receipt_verifier=RaisingVerifier(),
            memory=self.memory,
            repository=self.repository,
            classifier_artifact_sha256="a" * 64,
            policy_artifact_sha256="b" * 64,
            artifact_attestation=self.attestation,
            artifact_attestation_verifier=self.attestation_verifier,
            runtime_artifacts=self.runtime_artifacts,
        )
        result = service.capture_execution(
            self.decision, self.execution(), evidence_id="evidence:1",
            policy_version="policy:v1", next_command="Hold for verification",
        )
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)
        self.assertIsNone(result.adaptation)
        self.assertEqual(
            result.reasons,
            ("Independent receipt verification failed closed.",)
        )
        self.assertNotIn("RuntimeError", result.reasons[0])
        self.assertNotIn("private verifier endpoint/token detail", result.reasons[0])
        self.assertEqual(self.classifier.calls, 0)

    def test_rejected_decision_fails_closed(self):
        decision = DecisionItem(
            self.decision.id, self.decision.signal_kind, self.decision.severity,
            self.decision.problem, self.decision.recommended_action,
            self.decision.owner, "REJECTED",
        )
        result = self.capture(decision=decision)
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)
        self.assertEqual(self.memory.recent(), ())


if __name__ == "__main__":
    unittest.main()
