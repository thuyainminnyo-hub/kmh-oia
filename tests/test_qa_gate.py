"""Tests for the independent structural QA evidence gate."""
import json
import tempfile
import unittest
from pathlib import Path

from src.pilot import run_pilot
from src.qa_gate import evaluate_evidence, write_verdict


class IndependentQAGateTests(unittest.TestCase):
    def make_evidence(self, root: Path, goal: str = "QA expected output"):
        _, evidence, _ = run_pilot(
            goal,
            artifact_dir=root / "artifacts",
            evidence_path=root / "evidence.jsonl",
            session_id="qa-test",
        )
        return evidence

    def test_valid_artifact_passes_without_promoting_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root)
            verdict = evaluate_evidence(evidence, expected_output="QA expected output")
            self.assertEqual(verdict.status, "PASS")
            self.assertEqual(verdict.evidence_id, evidence.evidence_id)
            self.assertEqual(evidence.validation_state, "OBSERVED")
            self.assertTrue(all(check.passed for check in verdict.checks))

    def test_tampered_artifact_fails_digest_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root)
            path = Path(evidence.artifact_ref)
            path.write_bytes(path.read_bytes() + b"tampered")
            verdict = evaluate_evidence(evidence)
            self.assertEqual(verdict.status, "FAIL")
            self.assertIn("digest", verdict.reason)

    def test_missing_artifact_is_not_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root)
            Path(evidence.artifact_ref).unlink()
            verdict = evaluate_evidence(evidence)
            self.assertEqual(verdict.status, "NOT_VERIFIED")
            self.assertFalse(any(c.passed for c in verdict.checks))

    def test_expected_output_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root)
            verdict = evaluate_evidence(evidence, expected_output="not the real output")
            self.assertEqual(verdict.status, "FAIL")
            self.assertTrue(any(c.name == "expected_output_matches" and not c.passed for c in verdict.checks))

    def test_verdict_can_be_persisted_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root)
            verdict = evaluate_evidence(evidence)
            verdict_path = root / "qa" / "verdicts.jsonl"
            write_verdict(verdict, verdict_path)
            saved = json.loads(verdict_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(saved["qa_id"], verdict.qa_id)
            self.assertEqual(saved["evidence_id"], evidence.evidence_id)
            self.assertEqual(saved["status"], verdict.status)
            self.assertEqual(evidence.validation_state, "OBSERVED")


if __name__ == "__main__":
    unittest.main()
