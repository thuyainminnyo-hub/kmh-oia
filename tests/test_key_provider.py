"""Tests for the HMAC key provider interface and accepted-key policy."""
import tempfile
import unittest
from pathlib import Path

from src.governance_gate import decide_release
from src.key_provider import InMemoryKeyProvider, verify_with_provider
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
            signed = sign_decision(self.make_decision(Path(directory)), KEY_V2, key_id="key-v2")
            provider = InMemoryKeyProvider(
                keys={"key-v1": KEY_V1, "key-v2": KEY_V2},
                accepted_ids={"key-v2"},
            )
            self.assertTrue(verify_with_provider(signed, provider))

    def test_retired_key_id_is_rejected_even_if_key_remains_available(self):
        with tempfile.TemporaryDirectory() as directory:
            signed = sign_decision(self.make_decision(Path(directory)), KEY_V1, key_id="key-v1")
            provider = InMemoryKeyProvider(
                keys={"key-v1": KEY_V1, "key-v2": KEY_V2},
                accepted_ids={"key-v2"},
            )
            self.assertFalse(verify_with_provider(signed, provider))

    def test_unknown_key_or_provider_interface_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            signed = sign_decision(self.make_decision(Path(directory)), KEY_V2, key_id="key-v2")
            provider = InMemoryKeyProvider(keys={}, accepted_ids={"key-v2"})
            self.assertFalse(verify_with_provider(signed, provider))
            self.assertFalse(verify_with_provider(signed, object()))


if __name__ == "__main__":
    unittest.main()
