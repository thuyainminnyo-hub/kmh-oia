import unittest

from src.trusted_source_receipt import (
    TrustedSourceReceipt,
    TrustedSourceReceiptVerifier,
)


class FakeTrustedSourceAdapter:
    provider_name = "booking-provider"

    def __init__(self, *, integrity_ok=True, attribution_ok=True, receipt=None):
        self.integrity_ok = integrity_ok
        self.attribution_ok = attribution_ok
        self.receipt_override = receipt

    def fetch_receipt(self, source_record_id, execution_id):
        if self.receipt_override is not None:
            return self.receipt_override
        return TrustedSourceReceipt(
            provider_name=self.provider_name,
            source_record_id=source_record_id,
            execution_id=execution_id,
            raw_observation="booking_id=42;status=confirmed",
            observed_at="2026-10-20T10:00:00Z",
            content_hash="sha256:test-fixture",
            verification_method="fake-adapter-test",
        )

    def verify_receipt(self, receipt):
        return self.integrity_ok

    def match_execution(self, receipt, execution_id):
        return self.attribution_ok and receipt.execution_id == execution_id


class TrustedSourceReceiptVerifierTests(unittest.TestCase):
    def verifier(self, adapter=None, allowed=("booking-provider",)):
        return TrustedSourceReceiptVerifier(adapter, allowed_providers=allowed)

    def test_valid_allowlisted_receipt_passes_integrity_and_attribution(self):
        result = self.verifier(FakeTrustedSourceAdapter()).verify("booking:42", "exec:1")
        self.assertTrue(result.verified)
        self.assertEqual(result.provider_name, "booking-provider")
        self.assertEqual(result.source_record_id, "booking:42")
        self.assertEqual(result.execution_id, "exec:1")
        self.assertEqual(result.raw_observation, "booking_id=42;status=confirmed")

    def test_missing_adapter_fails_closed(self):
        result = self.verifier(None).verify("booking:42", "exec:1")
        self.assertFalse(result.verified)
        self.assertIn("No trusted source adapter", result.reasons[0])

    def test_unallowlisted_provider_fails_closed(self):
        result = self.verifier(FakeTrustedSourceAdapter(), allowed=("other-provider",)).verify(
            "booking:42", "exec:1"
        )
        self.assertFalse(result.verified)
        self.assertIn("not allowlisted", result.reasons[0])

    def test_invalid_receipt_integrity_fails_closed(self):
        result = self.verifier(FakeTrustedSourceAdapter(integrity_ok=False)).verify(
            "booking:42", "exec:1"
        )
        self.assertFalse(result.verified)
        self.assertIn("integrity/authenticity", result.reasons[0])

    def test_attribution_mismatch_fails_closed(self):
        result = self.verifier(FakeTrustedSourceAdapter(attribution_ok=False)).verify(
            "booking:42", "exec:1"
        )
        self.assertFalse(result.verified)
        self.assertIn("attribution", result.reasons[0])

    def test_receipt_for_different_execution_fails_closed(self):
        wrong_execution = TrustedSourceReceipt(
            provider_name="booking-provider",
            source_record_id="booking:42",
            execution_id="exec:other",
            raw_observation="booking_id=42;status=confirmed",
            observed_at="2026-10-20T10:00:00Z",
            content_hash="sha256:test-fixture",
            verification_method="fake-adapter-test",
        )
        result = self.verifier(
            FakeTrustedSourceAdapter(receipt=wrong_execution)
        ).verify("booking:42", "exec:1")
        self.assertFalse(result.verified)
        self.assertIn("not linked", result.reasons[0])

    def test_missing_raw_observation_fails_closed(self):
        missing_observation = TrustedSourceReceipt(
            provider_name="booking-provider",
            source_record_id="booking:42",
            execution_id="exec:1",
            raw_observation=" ",
            observed_at="2026-10-20T10:00:00Z",
            content_hash="sha256:test-fixture",
            verification_method="fake-adapter-test",
        )
        result = self.verifier(
            FakeTrustedSourceAdapter(receipt=missing_observation)
        ).verify("booking:42", "exec:1")
        self.assertFalse(result.verified)
        self.assertIn("raw observation is missing", result.reasons[0])


if __name__ == "__main__":
    unittest.main()
