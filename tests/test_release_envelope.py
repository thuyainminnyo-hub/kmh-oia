"""Tests for integrity checks over release decision envelopes."""
import copy
import tempfile
import unittest
from pathlib import Path

from src.governance_gate import decide_release
from src.pilot import run_pilot
from src.qa_gate import evaluate_evidence
from src.release_envelope import create_envelope, verify_envelope
from src.release_enforcer import require_release_allowed


class ReleaseEnvelopeTests(unittest.TestCase):
    def make_decision(self, root: Path):
        _, evidence, _ = run_pilot(
            "decision envelope output",
            artifact_dir=root / "artifacts",
            evidence_path=root / "evidence.jsonl",
            source_revision="d" * 40,
        )
        qa = evaluate_evidence(evidence, expected_output="decision envelope output")
        return decide_release(
            evidence,
            qa,
            expected_source_revision="d" * 40,
            actual_source_revision="d" * 40,
            approval_id="approval:envelope-001",
            approver_id="reviewer:001",
            approver_authorized=True,
        )

    def test_envelope_for_valid_decision_verifies(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_decision(Path(directory))
            envelope = create_envelope(decision)
            self.assertTrue(verify_envelope(envelope))
            self.assertTrue(verify_envelope(envelope.to_dict()))

    def test_tampered_decision_body_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            envelope = create_envelope(self.make_decision(Path(directory))).to_dict()
            changed = copy.deepcopy(envelope)
            changed["decision"]["status"] = "BLOCK"
            self.assertFalse(verify_envelope(changed))

    def test_tampered_digest_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            envelope = create_envelope(self.make_decision(Path(directory))).to_dict()
            envelope["decision_sha256"] = "0" * 64
            self.assertFalse(verify_envelope(envelope))

    def test_wrong_schema_and_malformed_envelopes_fail_closed(self):
        self.assertFalse(verify_envelope({"schema_version": "2.0", "decision": {}, "decision_sha256": "a"}))
        self.assertFalse(verify_envelope({"schema_version": "1.0", "decision": [], "decision_sha256": "a"}))
        self.assertFalse(verify_envelope(None))

    def test_release_enforcer_rejects_mutated_in_memory_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_decision(Path(directory))
            decision.checks[0]["passed"] = False
            with self.assertRaises(Exception):
                require_release_allowed(decision)


if __name__ == "__main__":
    unittest.main()
