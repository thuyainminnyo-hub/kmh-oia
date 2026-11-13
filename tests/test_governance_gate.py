"""Tests for the fail-closed release governance gate."""
import tempfile
import unittest
from pathlib import Path

from src.evidence_object import EvidenceObject
from src.governance_gate import decide_release, write_decision
from src.pilot import run_pilot
from src.qa_gate import evaluate_evidence


class GovernanceGateTests(unittest.TestCase):
    def make_evidence(self, root: Path, revision: str = "a" * 40):
        _, evidence, _ = run_pilot(
            "release gate test",
            artifact_dir=root / "artifacts",
            evidence_path=root / "evidence.jsonl",
            session_id="governance-test",
            source_revision=revision,
        )
        return evidence

    def decide(self, evidence, verdict, **overrides):
        args = {
            "expected_source_revision": "a" * 40,
            "actual_source_revision": "a" * 40,
            "approval_id": "approval:review-001",
            "approver_id": "reviewer:authorized-001",
            "approver_authorized": True,
        }
        args.update(overrides)
        return decide_release(evidence, verdict, **args)

    def test_all_gates_pass_allows_decision_but_keeps_evidence_observed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root)
            qa = evaluate_evidence(evidence, expected_output="release gate test")
            decision = self.decide(evidence, qa)
            self.assertEqual(decision.status, "ALLOW")
            self.assertEqual(evidence.validation_state, "OBSERVED")
            self.assertTrue(all(check["passed"] for check in decision.checks))

    def test_missing_qa_blocks_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root)
            decision = self.decide(evidence, None)
            self.assertEqual(decision.status, "BLOCK")

    def test_revision_mismatch_blocks_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root)
            qa = evaluate_evidence(evidence)
            decision = self.decide(evidence, qa, actual_source_revision="b" * 40)
            self.assertEqual(decision.status, "BLOCK")
            self.assertFalse(next(c for c in decision.checks if c["name"] == "source_revision_matches_runtime")["passed"])

    def test_unresolved_revision_blocks_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root, revision="unresolved")
            qa = evaluate_evidence(evidence)
            decision = self.decide(evidence, qa)
            self.assertEqual(decision.status, "BLOCK")

    def test_unauthorized_or_missing_approval_blocks_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root)
            qa = evaluate_evidence(evidence)
            for kwargs in (
                {"approver_authorized": False},
                {"approval_id": None},
                {"approver_id": None},
            ):
                with self.subTest(kwargs=kwargs):
                    decision = self.decide(evidence, qa, **kwargs)
                    self.assertEqual(decision.status, "BLOCK")

    def test_qa_for_different_evidence_blocks_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root)
            other = EvidenceObject(
                evidence_id="evidence:other",
                kind=evidence.kind,
                source=evidence.source,
                observed_at=evidence.observed_at,
                scope=evidence.scope,
                source_revision=evidence.source_revision,
                artifact_ref=evidence.artifact_ref,
                sha256_digest=evidence.sha256_digest,
                run_id="different-run",
                trace_id="different-trace",
                validation_state="OBSERVED",
            )
            qa = evaluate_evidence(other)
            decision = self.decide(evidence, qa)
            self.assertEqual(decision.status, "BLOCK")

    def test_release_decision_is_persisted_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = self.make_evidence(root)
            qa = evaluate_evidence(evidence)
            decision = self.decide(evidence, qa)
            destination = root / "audit" / "release.jsonl"
            write_decision(decision, destination)
            self.assertIn('"status": "ALLOW"', destination.read_text(encoding="utf-8"))
            self.assertEqual(evidence.validation_state, "OBSERVED")


if __name__ == "__main__":
    unittest.main()
