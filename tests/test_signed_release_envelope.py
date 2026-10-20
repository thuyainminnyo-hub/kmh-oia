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
    sign_decision,
    verify_signed_envelope,
)


KEY = b"test-only-kmh-oia-release-key-32-bytes-minimum"
OTHER_KEY = b"not-the-same-key-for-release-gate-tests"


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

    def test_short_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_decision(Path(directory))
            with self.assertRaisesRegex(ValueError, "at least 32"):
                sign_decision(decision, b"short")


if __name__ == "__main__":
    unittest.main()
