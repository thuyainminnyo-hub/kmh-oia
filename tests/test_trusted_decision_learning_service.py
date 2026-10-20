import unittest
from datetime import datetime, timezone

from src.decision_queue import DecisionItem
from src.evidence_admission_gate import EvidenceAdmissionResult
from src.live_runtime_bridge import ExecutionRecord
from src.operating_loop_record import OperatingLoopRecord
from src.operating_memory import OperatingMemory
from src.trusted_decision_learning_service import (
    TrustedDecisionLearningService,
    TrustedOutcomeClassification,
)
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
            content_hash=f"sha256:receipt-{self.calls}",
            verification_method="test-provider-signature-and-attribution",
        )

    def verify_receipt(self, receipt):
        return receipt.content_hash.startswith("sha256:")

    def match_execution(self, receipt, execution_id):
        return receipt.execution_id == execution_id


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
        self.memory = OperatingMemory()
        self.classifier = TestClassifier()
        self.adapter = FakeTrustedSourceAdapter()
        self.verifier = TrustedSourceReceiptVerifier(
            self.adapter,
            allowed_providers=("booking-provider",),
        )
        self.service = TrustedDecisionLearningService(
            classifier=self.classifier,
            receipt_verifier=self.verifier,
            memory=self.memory,
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
        )
        result = receipt_result
        if receipt and result is None:
            result = ReceiptVerificationResult(
                verified=True, provider_name="booking-provider",
                source_record_id="record:1", execution_id="exec:1",
                raw_observation="booking outcome=failed",
                verification_method="test-provider-signature-and-attribution",
                reasons=("test receipt",),
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
        self.assertEqual(len(self.memory.recent()), 1)
        self.assertEqual(self.adapter.calls, 1)
        with self.assertRaisesRegex(ValueError, "only approved adaptations can be applied"):
            self.service._adaptation_engine.apply(result.adaptation)

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
            classifier=None, receipt_verifier=self.verifier, memory=self.memory
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
            classifier=self.classifier, receipt_verifier=None, memory=self.memory
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

    def test_classifier_failure_fails_closed(self):
        self.classifier.error = RuntimeError("classification unavailable")
        result = self.capture()
        self.assertFalse(result.admitted)
        self.assertIsNone(result.memory)
        self.assertIsNone(result.adaptation)
        self.assertEqual(self.memory.recent(), ())

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
