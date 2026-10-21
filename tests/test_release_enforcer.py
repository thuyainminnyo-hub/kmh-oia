"""Tests for the fail-closed release enforcement adapter."""
import tempfile
import unittest
from pathlib import Path

from src.governance_gate import ReleaseDecision, decide_release
from src.pilot import run_pilot
from src.qa_gate import evaluate_evidence
from src.release_enforcer import ReleaseBlocked, require_release_allowed


class ReleaseEnforcerTests(unittest.TestCase):
    def _allowed_decision(self, root: Path):
        _, evidence, _ = run_pilot(
            "release enforcer check",
            artifact_dir=root / "artifacts",
            evidence_path=root / "evidence.jsonl",
            source_revision="c" * 40,
        )
        qa = evaluate_evidence(evidence, expected_output="release enforcer check")
        return decide_release(
            evidence,
            qa,
            expected_source_revision="c" * 40,
            actual_source_revision="c" * 40,
            approval_id="approval:001",
            approver_id="reviewer:001",
            approver_authorized=True,
        )

    def test_allow_decision_passes_enforcement_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self._allowed_decision(Path(directory))
            self.assertEqual(decision.status, "ALLOW")
            require_release_allowed(decision)

    def test_block_decision_raises_and_prevents_following_action(self):
        with tempfile.TemporaryDirectory() as directory:
            _, evidence, _ = run_pilot(
                "blocked release test",
                artifact_dir=Path(directory) / "artifacts",
                evidence_path=Path(directory) / "evidence.jsonl",
                source_revision="c" * 40,
            )
            decision = decide_release(
                evidence, None,
                expected_source_revision="c" * 40,
                actual_source_revision="c" * 40,
                approval_id=None,
                approver_id=None,
                approver_authorized=False,
            )
            action_log = []
            with self.assertRaises(ReleaseBlocked):
                require_release_allowed(decision)
                action_log.append("deploy")
            self.assertEqual(action_log, [])

    def test_allow_with_missing_or_failed_checks_is_rejected(self):
        forged_incomplete = ReleaseDecision(
            decision_id="decision:incomplete",
            evidence_id="evidence:001",
            qa_id="qa:001",
            status="ALLOW",
            decided_at="2026-10-20T00:00:00Z",
            checks=(),
            reason="forged incomplete record",
            approver_id="reviewer:001",
            source_revision_verified=True,
        )
        with self.assertRaises(ReleaseBlocked):
            require_release_allowed(forged_incomplete)

    def test_wrong_input_type_is_rejected(self):
        with self.assertRaises(TypeError):
            require_release_allowed({"status": "ALLOW"})


if __name__ == "__main__":
    unittest.main()
