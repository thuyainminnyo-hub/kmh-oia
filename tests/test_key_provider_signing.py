"""End-to-end controlled tests for key-provider-backed signed decisions."""
import copy
import tempfile
import unittest
from pathlib import Path

from src.governance_gate import decide_release
from src.key_provider_signing import (
    KeyProviderSigningError,
    require_provider_signed_release_allowed,
    sign_decision_with_provider,
)
from src.pilot import run_pilot
from src.qa_gate import evaluate_evidence
from src.trusted_key_provider import InMemoryTrustedKeyProvider


KEY_V1 = b"kmh-oia-test-provider-key-v1-minimum-32-bytes"
KEY_V2 = b"kmh-oia-test-provider-key-v2-minimum-32-bytes"


class KeyProviderSigningTests(unittest.TestCase):
    def make_decision(self, root: Path, source_revision: str = "1" * 40, approved: bool = True):
        _, evidence, _ = run_pilot(
            "provider integrated release",
            artifact_dir=root / "artifacts",
            evidence_path=root / "evidence.jsonl",
            source_revision=source_revision,
        )
        qa = evaluate_evidence(evidence, expected_output="provider integrated release")
        return decide_release(
            evidence,
            qa,
            expected_source_revision="1" * 40,
            actual_source_revision="1" * 40,
            approval_id="approval:provider-01" if approved else None,
            approver_id="reviewer:provider-01" if approved else None,
            approver_authorized=approved,
        )

    def provider(self):
        return InMemoryTrustedKeyProvider(
            {"key-v1": KEY_V1}, "key-v1", {"key-v1"}
        )

    def test_provider_signs_and_verifies_allowed_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = self.provider()
            decision = self.make_decision(Path(directory))
            signed = sign_decision_with_provider(provider, decision)
            self.assertEqual(signed.key_id, "key-v1")
            allowed = require_provider_signed_release_allowed(provider, signed)
            self.assertEqual(allowed.status, "ALLOW")

    def test_retired_key_is_rejected_before_release(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = self.provider()
            signed = sign_decision_with_provider(provider, self.make_decision(Path(directory)))
            provider.rotate(
                new_key_id="key-v2", new_secret=KEY_V2,
                accepted_key_ids={"key-v2"},
            )
            with self.assertRaisesRegex(KeyProviderSigningError, "retired"):
                require_provider_signed_release_allowed(provider, signed)

    def test_modified_signature_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = self.provider()
            signed = sign_decision_with_provider(provider, self.make_decision(Path(directory))).to_dict()
            signed["hmac_sha256"] = "0" * 64
            with self.assertRaisesRegex(KeyProviderSigningError, "rejected"):
                require_provider_signed_release_allowed(provider, signed)

    def test_signed_block_decision_does_not_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = self.provider()
            signed = sign_decision_with_provider(
                provider, self.make_decision(Path(directory), approved=False)
            )
            with self.assertRaises(KeyProviderSigningError):
                require_provider_signed_release_allowed(provider, signed)

    def test_unavailable_active_signing_key_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = self.provider()
            provider._keyring.pop("key-v1")
            with self.assertRaisesRegex(KeyProviderSigningError, "unavailable"):
                sign_decision_with_provider(provider, self.make_decision(Path(directory)))


if __name__ == "__main__":
    unittest.main()
