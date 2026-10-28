"""Tests for HMAC-authenticated release decisions."""
import copy
import tempfile
import unittest
from pathlib import Path

from src.governance_gate import decide_release
from src.pilot import run_pilot
from src.qa_gate import evaluate_evidence
from src.signed_release_envelope import (
    require_signed_release_allowed,
    require_release_allowed_with_keyring,
    sign_decision,
    verify_signed_envelope,
    verify_with_keyring,
)


KEY = b"test-only-kmh-oia-release-key-32-bytes-minimum"
OTHER_KEY = b"not-the-same-key-for-release-gate-tests"
ROTATED_KEY = b"kmh-oia-rotated-key-two-test-only-32-bytes"


class SignedReleaseEnvelopeTests(unittest.TestCase):
    def make_decision(self, root: Path, allow: bool = True):
        _, evidence, _ = run_pilot(
            "signed release envelope",
            artifact_dir=root / "artifacts",
            evidence_path=root / "evidence.jsonl",
            source_revision="f" * 40,
        )
        qa = evaluate_evidence(evidence, expected_output="signed release envelope")
        return decide_release(
            evidence,
            qa,
            expected_source_revision="f" * 40,
            actual_source_revision="f" * 40,
            approval_id="approval:signed-001" if allow else None,
            approver_id="reviewer:signed-001" if allow else None,
            approver_authorized=allow,
        )

    def test_valid_signed_allow_envelope_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            signed = sign_decision(self.make_decision(Path(directory)), KEY)
            self.assertTrue(verify_signed_envelope(signed, KEY))
            decision = require_signed_release_allowed(signed, KEY)
            self.assertEqual(decision.status, "ALLOW")

    def test_wrong_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            signed = sign_decision(self.make_decision(Path(directory)), KEY)
            self.assertFalse(verify_signed_envelope(signed, OTHER_KEY))
            with self.assertRaisesRegex(ValueError, "signature"):
                require_signed_release_allowed(signed, OTHER_KEY)

    def test_tampered_decision_body_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            signed = sign_decision(self.make_decision(Path(directory)), KEY).to_dict()
            modified = copy.deepcopy(signed)
            modified["envelope"]["decision"]["status"] = "ALLOW"
            modified["envelope"]["decision"]["reason"] = "tampered"
            with self.assertRaisesRegex(ValueError, "signature"):
                require_signed_release_allowed(modified, KEY)

    def test_signed_block_decision_stays_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            signed = sign_decision(self.make_decision(Path(directory), allow=False), KEY)
            self.assertTrue(verify_signed_envelope(signed, KEY))
            with self.assertRaises(Exception):
                require_signed_release_allowed(signed, KEY)


    def test_key_rotation_accepts_old_key_only_during_overlap_window(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_decision(Path(directory))
            old_signed = sign_decision(decision, KEY, key_id="key-v1")
            keyring = {"key-v1": KEY, "key-v2": ROTATED_KEY}

            # Explicit overlap policy may accept the old key during migration.
            self.assertTrue(verify_with_keyring(old_signed, keyring, {"key-v1", "key-v2"}))
            self.assertEqual(
                require_release_allowed_with_keyring(old_signed, keyring, {"key-v1", "key-v2"}).status,
                "ALLOW",
            )

            # Retirement removes the key ID from the accepted set, even if
            # the old key is still present in the operational keyring.
            self.assertFalse(verify_with_keyring(old_signed, keyring, {"key-v2"}))
            with self.assertRaisesRegex(ValueError, "retired/untrusted"):
                require_release_allowed_with_keyring(old_signed, keyring, {"key-v2"})

            new_signed = sign_decision(decision, ROTATED_KEY, key_id="key-v2")
            self.assertTrue(verify_with_keyring(new_signed, keyring, {"key-v2"}))

    def test_signature_binds_key_id(self):
        with tempfile.TemporaryDirectory() as directory:
            signed = sign_decision(self.make_decision(Path(directory)), KEY, key_id="key-v1").to_dict()
            signed["key_id"] = "key-v2"
            self.assertFalse(verify_signed_envelope(signed, KEY))

    def test_blank_key_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_decision(Path(directory))
            with self.assertRaisesRegex(ValueError, "key_id"):
                sign_decision(decision, KEY, key_id="  ")

    def test_short_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_decision(Path(directory))
            with self.assertRaisesRegex(ValueError, "at least 32"):
                sign_decision(decision, b"short")


if __name__ == "__main__":
    unittest.main()
