"""Tests for envelope verification composed with release enforcement."""
import copy
import tempfile
import unittest
from pathlib import Path

from src.governance_gate import decide_release
from src.pilot import run_pilot
from src.qa_gate import evaluate_evidence
from src.release_envelope import create_envelope
from src.trusted_release_gate import require_trusted_release_allowed


class TrustedReleaseGateTests(unittest.TestCase):
    def make_envelope(self, root: Path, approval: bool = True):
        _, evidence, _ = run_pilot(
            "trusted release gate",
            artifact_dir=root / "artifacts",
            evidence_path=root / "evidence.jsonl",
            source_revision="e" * 40,
        )
        qa = evaluate_evidence(evidence, expected_output="trusted release gate")
        decision = decide_release(
            evidence,
            qa,
            expected_source_revision="e" * 40,
            actual_source_revision="e" * 40,
            approval_id="approval:trusted-01" if approval else None,
            approver_id="reviewer:01" if approval else None,
            approver_authorized=approval,
        )
        return create_envelope(decision).to_dict()

    def test_integrity_valid_allow_envelope_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            envelope = self.make_envelope(Path(directory))
            decision = require_trusted_release_allowed(envelope)
            self.assertEqual(decision.status, "ALLOW")

    def test_modified_body_is_rejected_before_enforcement(self):
        with tempfile.TemporaryDirectory() as directory:
            envelope = self.make_envelope(Path(directory))
            modified = copy.deepcopy(envelope)
            modified["decision"]["status"] = "ALLOW"
            modified["decision"]["reason"] = "force allow"
            with self.assertRaisesRegex(ValueError, "integrity"):
                require_trusted_release_allowed(modified)

    def test_valid_envelope_with_block_decision_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            envelope = self.make_envelope(Path(directory), approval=False)
            with self.assertRaises(Exception):
                require_trusted_release_allowed(envelope)

    def test_malformed_decision_shape_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            envelope = self.make_envelope(Path(directory))
            envelope["decision"]["unexpected_field"] = True
            # The body mutation also invalidates the envelope checksum.
            with self.assertRaisesRegex(ValueError, "integrity"):
                require_trusted_release_allowed(envelope)


if __name__ == "__main__":
    unittest.main()
