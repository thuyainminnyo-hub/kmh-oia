import unittest

from src.decision_outcome_evaluator import DecisionOutcome
from src.evidence_admission_gate import EvidenceAdmissionResult
from src.live_runtime_bridge import ExecutionRecord
from src.operating_loop_record import OperatingLoopRecord
from src.trusted_source_receipt import ReceiptVerificationResult
from src.verified_learning_admission import VerifiedLearningAdmission


class VerifiedLearningAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.outcome = DecisionOutcome(
            decision_id="decision:1",
            command_id="cmd:1",
            outcome_positive=False,
            quality="POOR",
            reason="Caller-supplied result; external verification is not established.",
        )

    def execution(self, *, admitted=True, receipt=True, final_status="LEARNED",
                  source_decision_id="decision:1", loop_command_id="cmd:1"):
        loop = OperatingLoopRecord(
            context_id="context:1",
            decision_id=source_decision_id,
            command_id=loop_command_id,
            execution_id="exec:1",
            trace_id="trace:1",
            qa_status="PASS",
            evidence_status="OUTCOME_LINKED" if admitted else "OBSERVED",
            learning_status="ADMITTED" if admitted else "NOT_ADMITTED",
            source_decision_id=source_decision_id,
        )
        gate = EvidenceAdmissionResult(
            decision="ADMITTED" if admitted else "NOT_ADMITTED",
            evidence_status="OUTCOME_LINKED" if admitted else "OBSERVED",
            learning_admitted=admitted,
            missing_fields=() if admitted else ("trusted_receipt_verification",),
            reasons=("test gate result",),
            receipt_content_hash="sha256:test-fixture" if admitted else "",
        )
        receipt_result = None
        if receipt:
            receipt_result = ReceiptVerificationResult(
                verified=True,
                provider_name="booking-provider",
                source_record_id="record:1",
                execution_id="exec:1",
                raw_observation="booking=confirmed",
                verification_method="test-adapter",
                reasons=("test receipt accepted",),
                content_hash="sha256:test-fixture",
            )
        return ExecutionRecord(
            command_id="cmd:1",
            response="done",
            trace_stages=("input_gateway", "evaluation"),
            evidence=("trace_id=trace:1",),
            qa_status="PASS",
            final_status=final_status,
            source_decision_id=source_decision_id,
            operating_loop=loop,
            admission=gate,
            trusted_receipt_verification=receipt_result,
        )

    def proof(self, execution=None, outcome=None):
        return VerifiedLearningAdmission.from_execution(
            outcome or self.outcome,
            execution or self.execution(),
            evidence_id="evidence:1",
            policy_version="policy:v1",
        )

    def test_matching_admitted_execution_produces_bound_proof(self):
        proof = self.proof()
        self.assertEqual(proof.decision_id, "decision:1")
        self.assertEqual(proof.command_id, "cmd:1")
        self.assertEqual(proof.execution_id, "exec:1")
        self.assertEqual(proof.trace_id, "trace:1")
        self.assertEqual(proof.provider_name, "booking-provider")
        self.assertEqual(proof.policy_version, "policy:v1")
        self.assertEqual(proof.receipt_content_hash, "sha256:test-fixture")

    def test_not_admitted_gate_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be ADMITTED"):
            self.proof(execution=self.execution(admitted=False))

    def test_missing_receipt_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "trusted receipt verification"):
            self.proof(execution=self.execution(receipt=False))

    def test_unlearned_execution_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "LEARNED execution"):
            self.proof(execution=self.execution(final_status="COMPLETED"))

    def test_source_decision_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "decision/command trace"):
            self.proof(execution=self.execution(source_decision_id="decision:other"))

    def test_execution_source_decision_is_checked_independently(self):
        execution = self.execution()
        execution = ExecutionRecord(
            command_id=execution.command_id,
            response=execution.response,
            trace_stages=execution.trace_stages,
            evidence=execution.evidence,
            qa_status=execution.qa_status,
            final_status=execution.final_status,
            source_decision_id="decision:other",
            operating_loop=execution.operating_loop,
            admission=execution.admission,
            trusted_receipt_verification=execution.trusted_receipt_verification,
        )
        with self.assertRaisesRegex(ValueError, "execution source_decision_id"):
            self.proof(execution=execution)

    def test_blank_receipt_hash_is_rejected(self):
        execution = self.execution()
        receipt = execution.trusted_receipt_verification
        invalid_receipt = ReceiptVerificationResult(
            verified=True,
            provider_name=receipt.provider_name,
            source_record_id=receipt.source_record_id,
            execution_id=receipt.execution_id,
            raw_observation=receipt.raw_observation,
            verification_method=receipt.verification_method,
            reasons=receipt.reasons,
            content_hash=" ",
        )
        execution = ExecutionRecord(
            command_id=execution.command_id,
            response=execution.response,
            trace_stages=execution.trace_stages,
            evidence=execution.evidence,
            qa_status=execution.qa_status,
            final_status=execution.final_status,
            source_decision_id=execution.source_decision_id,
            operating_loop=execution.operating_loop,
            admission=execution.admission,
            trusted_receipt_verification=invalid_receipt,
        )
        with self.assertRaisesRegex(ValueError, "content hash"):
            self.proof(execution=execution)

    def test_blank_policy_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "policy_version is required"):
            VerifiedLearningAdmission.from_execution(
                self.outcome, self.execution(),
                evidence_id="evidence:1", policy_version=" ",
            )


if __name__ == "__main__":
    unittest.main()
