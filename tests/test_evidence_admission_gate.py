import unittest

from src.evidence_admission_gate import (
    EvidenceAdmissionGate,
    EvidenceAdmissionRequest,
)


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

    def test_claimed_authentication_without_trusted_receipt_is_rejected(self):
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="booking_system:record-42",
                raw_observation="booking_id=record-42",
                interpretation="booking attributed to execution",
                verification_status="OUTCOME_LINKED",
                outcome_linked=True,
                source_authenticated=True,
                attribution_verified=True,
            )
        )
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)
        self.assertEqual(result.missing_fields, ())
        self.assertTrue(any("trusted source receipt" in reason.lower() for reason in result.reasons))

    def test_verified_trusted_receipt_can_be_admitted(self):
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="booking_system:record-42",
                raw_observation="booking_id=record-42",
                interpretation="booking attributed to execution",
                verification_status="OUTCOME_LINKED",
                outcome_linked=True,
                source_authenticated=True,
                attribution_verified=True,
                trusted_receipt_verified=True,
            )
        )
        self.assertEqual(result.decision, "ADMITTED")
        self.assertTrue(result.learning_admitted)
        self.assertEqual(result.missing_fields, ())

    def test_outcome_linked_status_without_source_authentication_is_rejected(self):
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="booking_system:record-42",
                raw_observation="booking_id=record-42",
                verification_status="OUTCOME_LINKED",
                outcome_linked=True,
                attribution_verified=True,
            )
        )
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)
        self.assertTrue(any("authentication" in reason.lower() for reason in result.reasons))

    def test_outcome_linked_status_without_attribution_is_rejected(self):
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="booking_system:record-42",
                raw_observation="booking_id=record-42",
                verification_status="OUTCOME_LINKED",
                outcome_linked=True,
                source_authenticated=True,
            )
        )
        self.assertEqual(result.decision, "NOT_ADMITTED")
        self.assertFalse(result.learning_admitted)
        self.assertTrue(any("attribution" in reason.lower() for reason in result.reasons))

    def test_outcome_link_flag_without_outcome_linked_status_is_rejected(self):
        result = self.gate.evaluate(
            EvidenceAdmissionRequest(
                execution_id="exec:1",
                source="booking_system:record-42",
                raw_observation="booking_id=record-42",
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
