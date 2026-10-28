"""Tests for trusted HMAC key provider selection and release enforcement."""
import tempfile
import unittest
from pathlib import Path

from src.governance_gate import decide_release
from src.key_provider import (
    InMemoryKeyProvider,
    require_release_allowed_with_provider,
    sign_with_provider,
    verify_with_provider,
)
from src.pilot import run_pilot
from src.qa_gate import evaluate_evidence
from src.signed_release_envelope import sign_decision


KEY_V1 = b"provider-test-key-v1-keep-this-test-only-32bytes"
KEY_V2 = b"provider-test-key-v2-keep-this-test-only-32bytes"


class KeyProviderTests(unittest.TestCase):
    def make_decision(self, root: Path):
        _, evidence, _ = run_pilot(
            "provider interface",
            artifact_dir=root / "artifacts",
            evidence_path=root / "evidence.jsonl",
            source_revision="a" * 40,
        )
        qa = evaluate_evidence(evidence, expected_output="provider interface")
        return decide_release(
            evidence, qa,
            expected_source_revision="a" * 40,
            actual_source_revision="a" * 40,
            approval_id="approval:provider-001",
            approver_id="reviewer:provider-001",
            approver_authorized=True,
        )

    def test_provider_resolves_active_key_and_accepts_envelope(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_decision(Path(directory))
            provider = InMemoryKeyProvider(
                keys={"key-v1": KEY_V1, "key-v2": KEY_V2},
                accepted_ids={"key-v2"},
                active_id="key-v2",
            )
            signed = sign_with_provider(decision, provider)
            self.assertEqual(signed.key_id, "key-v2")
            self.assertTrue(verify_with_provider(signed, provider))
            self.assertEqual(require_release_allowed_with_provider(signed, provider).status, "ALLOW")

    def test_retired_key_id_is_rejected_even_if_key_remains_available(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_decision(Path(directory))
            signed = sign_decision(decision, KEY_V1, key_id="key-v1")
            provider = InMemoryKeyProvider(
                keys={"key-v1": KEY_V1, "key-v2": KEY_V2},
                accepted_ids={"key-v2"},
                active_id="key-v2",
            )
            self.assertFalse(verify_with_provider(signed, provider))
            with self.assertRaisesRegex(ValueError, "retired/untrusted"):
                require_release_allowed_with_provider(signed, provider)

    def test_unknown_key_or_bad_provider_interface_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_decision(Path(directory))
            signed = sign_decision(decision, KEY_V2, key_id="key-v2")
            provider = InMemoryKeyProvider(keys={}, accepted_ids={"key-v2"}, active_id="key-v2")
            self.assertFalse(verify_with_provider(signed, provider))
            self.assertFalse(verify_with_provider(signed, object()))
            with self.assertRaises(TypeError):
                require_release_allowed_with_provider(signed, object())

    def test_signing_requires_active_key_in_accepted_set(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_decision(Path(directory))
            provider = InMemoryKeyProvider(
                keys={"key-v1": KEY_V1, "key-v2": KEY_V2},
                accepted_ids={"key-v1"},
                active_id="key-v2",
            )
            with self.assertRaisesRegex(ValueError, "not accepted"):
                sign_with_provider(decision, provider)

    def test_ambiguous_active_key_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_decision(Path(directory))
            provider = InMemoryKeyProvider(
                keys={"key-v1": KEY_V1, "key-v2": KEY_V2},
                accepted_ids={"key-v1", "key-v2"},
            )
            with self.assertRaisesRegex(ValueError, "no unambiguous active"):
                sign_with_provider(decision, provider)


if __name__ == "__main__":
    unittest.main()
