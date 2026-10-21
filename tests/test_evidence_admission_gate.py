import unittest

from src.evidence_admission_gate import (
    EvidenceAdmissionGate,
    EvidenceAdmissionRequest,
)
from src.trusted_source_receipt import ReceiptVerificationResult


class EvidenceAdmissionGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = EvidenceAdmissionGate()

    def test_missing_source_execution_or_observation_is_not_admitted(self):
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="",
                source="",
                raw_observation="",
                verification_status="OUTCOME_LINKED",
                outcome_linked=True,
            )
        )
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)
        self.assertEqual(
            result.missing_fields,
            ("execution_id", "source", "raw_observation"),
        )

    def test_observed_evidence_does_not_admit_learning(self):
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="platform:analytics",
                raw_observation="impressions=100",
                interpretation="early reach signal",
                verification_status="OBSERVED",
            )
        )
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)

    def test_verified_evidence_without_outcome_link_does_not_admit_learning(self):
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="platform:analytics",
                raw_observation="impressions=100",
                verification_status="VERIFIED",
            )
        )
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)

    def test_mapping_boolean_claims_cannot_bypass_trusted_verifier(self):
        result = self.gate.evaluate_mapping(
            {
                "execution_id": "exec:1",
                "source": "booking-provider:record-42",
                "raw_observation": "booking_id=42",
                "verification_status": "OUTCOME_LINKED",
                "outcome_linked": "true",
                "source_authenticated": "true",
                "attribution_verified": "true",
                "trusted_receipt_verified": "true",
            }
        )
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)
        self.assertTrue(any("trusted source receipt" in reason.lower() for reason in result.reasons))

    def test_matching_trusted_verifier_result_can_be_admitted(self):
        receipt_result = ReceiptVerificationResult(
            verified=True,
            provider_name="booking-provider",
            source_record_id="record-42",
            execution_id="exec:1",
            raw_observation="booking_id=42;status=confirmed",
            verification_method="test-verifier",
            reasons=("verified for unit test",),
            content_hash="sha256:test-fixture",
        )
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="booking-provider:record-42",
                raw_observation="booking_id=42;status=confirmed",
                interpretation="booking attributed to execution",
                verification_status="OUTCOME_LINKED",
                outcome_linked=True,
                trusted_receipt_verification=receipt_result,
            )
        )
        self.assertEqual(result.decision, "ADMITTED")
        self.assertTrue(result.learning_admitted)
        self.assertEqual(result.missing_fields, ())

    def test_verifier_result_for_different_execution_is_rejected(self):
        receipt_result = ReceiptVerificationResult(
            verified=True,
            provider_name="booking-provider",
            source_record_id="record-42",
            execution_id="exec:other",
            raw_observation="booking_id=42;status=confirmed",
            verification_method="test-verifier",
            reasons=("test fixture",),
            content_hash="sha256:test-fixture",
        )
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="booking-provider:record-42",
                raw_observation="booking_id=42;status=confirmed",
                verification_status="OUTCOME_LINKED",
                outcome_linked=True,
                trusted_receipt_verification=receipt_result,
            )
        )
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)

    def test_verifier_result_with_mismatched_raw_observation_is_rejected(self):
        receipt_result = ReceiptVerificationResult(
            verified=True,
            provider_name="booking-provider",
            source_record_id="record-42",
            execution_id="exec:1",
            raw_observation="booking_id=42;status=confirmed",
            verification_method="test-verifier",
            reasons=("test fixture",),
        )
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="booking-provider:record-42",
                raw_observation="caller-edited observation",
                verification_status="OUTCOME_LINKED",
                outcome_linked=True,
                trusted_receipt_verification=receipt_result,
            )
        )
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)


    def test_verifier_result_without_content_hash_is_rejected(self):
        receipt_result = ReceiptVerificationResult(
            verified=True,
            provider_name="booking-provider",
            source_record_id="record-42",
            execution_id="exec:1",
            raw_observation="booking_id=42;status=confirmed",
            verification_method="test-verifier",
            reasons=("fixture with missing digest",),
        )
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="booking-provider:record-42",
                raw_observation="booking_id=42;status=confirmed",
                verification_status="OUTCOME_LINKED",
                outcome_linked=True,
                trusted_receipt_verification=receipt_result,
            )
        )
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)
        self.assertTrue(any("does not match" in reason.lower() for reason in result.reasons))

    def test_outcome_link_flag_without_outcome_linked_status_is_rejected(self):
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="booking-provider:record-42",
                raw_observation="booking_id=42",
                verification_status="VERIFIED",
                outcome_linked=True,
            )
        )
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)

    def test_unknown_status_is_conservative(self):
        result = self.gate.evaluate_mapping(
            {
                "execution_id": "exec:1",
                "source": "platform:analytics",
                "raw_observation": "clicks=10",
                "verification_status": "MADE_UP",
                "outcome_linked": "true",
            }
        )
        self.assertEqual(result.evidence_status, "UNKNOWN")
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)
        self.assertTrue(any("Unrecognized" in reason for reason in result.reasons))


if __name__ == "__main__":
    unittest.main()
