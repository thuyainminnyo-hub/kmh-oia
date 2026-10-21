import unittest
from datetime import datetime, timezone

from src.trusted_source_receipt import (
    TrustedSourceReceipt,
    TrustedSourceReceiptVerifier,
)
from src.receipt_replay_store import InMemoryReceiptReplayStore


FIXED_NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)


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
            observed_at="2026-10-20T11:30:00Z",
            content_hash="sha256:test-fixture",
            verification_method="fake-adapter-test",
        )

    def verify_receipt(self, receipt):
        return self.integrity_ok

    def match_execution(self, receipt, execution_id):
        return self.attribution_ok and receipt.execution_id == execution_id


class TrustedSourceReceiptVerifierTests(unittest.TestCase):
    def verifier(self, adapter=None, allowed=("booking-provider",), max_age=86400, replay_store=None):
        return TrustedSourceReceiptVerifier(
            adapter,
            allowed_providers=allowed,
            max_receipt_age_seconds=max_age,
            clock=lambda: FIXED_NOW,
            replay_store=replay_store,
        )

    def test_valid_allowlisted_fresh_receipt_passes(self):
        result = self.verifier(FakeTrustedSourceAdapter()).verify("booking:42", "exec:1")
        self.assertTrue(result.verified)
        self.assertEqual(result.provider_name, "booking-provider")
        self.assertEqual(result.source_record_id, "booking:42")
        self.assertEqual(result.execution_id, "exec:1")
        self.assertEqual(result.raw_observation, "booking_id=42;status=confirmed")
        self.assertEqual(result.content_hash, "sha256:test-fixture")


    def test_content_hash_must_match_recomputed_receipt_payload_digest(self):
        import hashlib

        class DigestCheckingAdapter(FakeTrustedSourceAdapter):
            def verify_receipt(self, receipt):
                expected = "sha256:" + hashlib.sha256(receipt.raw_observation.encode("utf-8")).hexdigest()
                return receipt.content_hash == expected

        raw = "booking_id=42;status=confirmed"
        good_hash = "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
        valid = TrustedSourceReceipt(
            provider_name="booking-provider",
            source_record_id="booking:42",
            execution_id="exec:1",
            raw_observation=raw,
            observed_at="2026-10-20T11:30:00Z",
            content_hash=good_hash,
            verification_method="test-sha256-payload-digest",
        )
        accepted = self.verifier(
            DigestCheckingAdapter(receipt=valid)
        ).verify("booking:42", "exec:1")
        self.assertTrue(accepted.verified)
        self.assertEqual(accepted.content_hash, good_hash)

        tampered = TrustedSourceReceipt(
            provider_name=valid.provider_name,
            source_record_id=valid.source_record_id,
            execution_id=valid.execution_id,
            raw_observation="booking_id=42;status=cancelled",
            observed_at=valid.observed_at,
            content_hash=good_hash,
            verification_method=valid.verification_method,
        )
        rejected = self.verifier(
            DigestCheckingAdapter(receipt=tampered)
        ).verify("booking:42", "exec:1")
        self.assertFalse(rejected.verified)
        self.assertIn("integrity/authenticity", rejected.reasons[0])

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
            observed_at="2026-10-20T11:30:00Z",
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
            observed_at="2026-10-20T11:30:00Z",
            content_hash="sha256:test-fixture",
            verification_method="fake-adapter-test",
        )
        result = self.verifier(
            FakeTrustedSourceAdapter(receipt=missing_observation)
        ).verify("booking:42", "exec:1")
        self.assertFalse(result.verified)
        self.assertIn("raw observation is missing", result.reasons[0])

    def test_stale_receipt_fails_closed(self):
        stale = TrustedSourceReceipt(
            provider_name="booking-provider",
            source_record_id="booking:42",
            execution_id="exec:1",
            raw_observation="booking_id=42;status=confirmed",
            observed_at="2026-10-18T11:30:00Z",
            content_hash="sha256:test-fixture",
            verification_method="fake-adapter-test",
        )
        result = self.verifier(
            FakeTrustedSourceAdapter(receipt=stale), max_age=3600
        ).verify("booking:42", "exec:1")
        self.assertFalse(result.verified)
        self.assertIn("stale", result.reasons[0])

    def test_future_receipt_timestamp_fails_closed(self):
        future = TrustedSourceReceipt(
            provider_name="booking-provider",
            source_record_id="booking:42",
            execution_id="exec:1",
            raw_observation="booking_id=42;status=confirmed",
            observed_at="2026-10-20T12:01:00Z",
            content_hash="sha256:test-fixture",
            verification_method="fake-adapter-test",
        )
        result = self.verifier(
            FakeTrustedSourceAdapter(receipt=future)
        ).verify("booking:42", "exec:1")
        self.assertFalse(result.verified)
        self.assertIn("future", result.reasons[0])

    def test_timezone_free_timestamp_fails_closed(self):
        no_timezone = TrustedSourceReceipt(
            provider_name="booking-provider",
            source_record_id="booking:42",
            execution_id="exec:1",
            raw_observation="booking_id=42;status=confirmed",
            observed_at="2026-10-20T11:30:00",
            content_hash="sha256:test-fixture",
            verification_method="fake-adapter-test",
        )
        result = self.verifier(
            FakeTrustedSourceAdapter(receipt=no_timezone)
        ).verify("booking:42", "exec:1")
        self.assertFalse(result.verified)
        self.assertIn("timezone", result.reasons[0])

    def test_invalid_timestamp_fails_closed(self):
        invalid = TrustedSourceReceipt(
            provider_name="booking-provider",
            source_record_id="booking:42",
            execution_id="exec:1",
            raw_observation="booking_id=42;status=confirmed",
            observed_at="not-a-time",
            content_hash="sha256:test-fixture",
            verification_method="fake-adapter-test",
        )
        result = self.verifier(
            FakeTrustedSourceAdapter(receipt=invalid)
        ).verify("booking:42", "exec:1")
        self.assertFalse(result.verified)
        self.assertIn("invalid", result.reasons[0])



    def test_same_receipt_cannot_be_admitted_twice(self):
        replay_store = InMemoryReceiptReplayStore()
        first = self.verifier(
            FakeTrustedSourceAdapter(), replay_store=replay_store
        ).verify("booking:42", "exec:1")
        second = self.verifier(
            FakeTrustedSourceAdapter(), replay_store=replay_store
        ).verify("booking:42", "exec:1")
        self.assertTrue(first.verified)
        self.assertFalse(second.verified)
        self.assertIn("replay", second.reasons[0].lower())


    def test_revalidation_can_skip_second_replay_claim(self):
        replay_store = InMemoryReceiptReplayStore()
        verifier = self.verifier(FakeTrustedSourceAdapter(), replay_store=replay_store)
        first = verifier.verify("booking:42", "exec:1")
        second = verifier.verify("booking:42", "exec:1", claim_replay=False)
        self.assertTrue(first.verified)
        self.assertTrue(second.verified)
        self.assertEqual(first.content_hash, second.content_hash)

    def test_revalidation_still_checks_authenticity_without_replay_claim(self):
        replay_store = InMemoryReceiptReplayStore()
        verifier = self.verifier(
            FakeTrustedSourceAdapter(integrity_ok=False),
            replay_store=replay_store,
        )
        result = verifier.verify("booking:42", "exec:1", claim_replay=False)
        self.assertFalse(result.verified)
        self.assertIn("integrity/authenticity", result.reasons[0])

    def test_replay_store_exception_fails_closed(self):
        class BrokenReplayStore:
            def claim(self, provider_name, source_record_id, content_hash):
                raise OSError("database unavailable")

        result = self.verifier(
            FakeTrustedSourceAdapter(), replay_store=BrokenReplayStore()
        ).verify("booking:42", "exec:1")
        self.assertFalse(result.verified)
        self.assertIn("Replay store unavailable", result.reasons[0])
        self.assertIn("OSError", result.reasons[0])


if __name__ == "__main__":
    unittest.main()
