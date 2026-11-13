"""Integration tests for the approval-gated release decision path."""
import tempfile
import unittest
from pathlib import Path

from src.approval_gated_release import decide_release_with_approval
from src.approval_policy import ApprovalRecord
from src.pilot import run_pilot
from src.qa_gate import evaluate_evidence


class FakeAuthority:
    def __init__(self, record=None, authorized=True, fail=False):
        self.record = record
        self.authorized = authorized
        self.fail = fail

    def resolve_approval(self, approval_id):
        if self.fail:
            raise RuntimeError("approval service unavailable")
        return self.record

    def is_authorized_approver(self, approver_id, policy_id):
        if self.fail:
            raise RuntimeError("identity service unavailable")
        return self.authorized


class ApprovalGatedReleaseTests(unittest.TestCase):
    def setup_case(self, root, approver="human:reviewer-1", decision="APPROVE", authorized=True):
        _, evidence, _ = run_pilot(
            "approval integration",
            artifact_dir=root / "artifacts",
            evidence_path=root / "evidence.jsonl",
            session_id="approval-gate-test",
            source_revision="a" * 40,
        )
        qa = evaluate_evidence(evidence, expected_output="approval integration")
        record = ApprovalRecord(
            approval_id="approval:101",
            approver_id=approver,
            evidence_id=evidence.evidence_id,
            qa_id=qa.qa_id,
            source_revision="a" * 40,
            decision=decision,
            policy_id="release-policy:v1",
            approved_at="2026-10-21T02:00:00Z",
        )
        authority = FakeAuthority(record=record, authorized=authorized)
        return evidence, qa, authority

    def decide(self, evidence, qa, authority, **overrides):
        args = dict(
            expected_source_revision="a" * 40,
            actual_source_revision="a" * 40,
            approval_authority=authority,
            approval_id="approval:101",
            signing_service_id="service:release-signer",
            accepted_policy_ids={"release-policy:v1"},
        )
        args.update(overrides)
        return decide_release_with_approval(evidence, qa, **args)

    def test_matching_independent_approval_allows_release(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence, qa, authority = self.setup_case(Path(directory))
            decision = self.decide(evidence, qa, authority)
            self.assertEqual(decision.status, "ALLOW")
            self.assertEqual(decision.approver_id, "human:reviewer-1")
            self.assertTrue(all(check["passed"] for check in decision.checks))

    def test_approver_same_as_signer_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence, qa, authority = self.setup_case(
                Path(directory), approver="service:release-signer"
            )
            decision = self.decide(evidence, qa, authority)
            self.assertEqual(decision.status, "BLOCK")
            self.assertFalse(next(c for c in decision.checks if c["name"]=="independent_approval_verified")["passed"])

    def test_rejected_or_unavailable_approval_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence, qa, authority = self.setup_case(Path(directory), decision="REJECT")
            self.assertEqual(self.decide(evidence, qa, authority).status, "BLOCK")
        with tempfile.TemporaryDirectory() as directory:
            evidence, qa, authority = self.setup_case(Path(directory))
            authority.fail = True
            self.assertEqual(self.decide(evidence, qa, authority).status, "BLOCK")

    def test_unapproved_source_revision_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence, qa, authority = self.setup_case(Path(directory))
            decision = self.decide(evidence, qa, authority, actual_source_revision="b"*40)
            self.assertEqual(decision.status, "BLOCK")

    def test_wrong_policy_or_unauthorized_approver_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence, qa, authority = self.setup_case(Path(directory), authorized=False)
            self.assertEqual(self.decide(evidence, qa, authority).status, "BLOCK")
        with tempfile.TemporaryDirectory() as directory:
            evidence, qa, authority = self.setup_case(Path(directory))
            decision = self.decide(evidence, qa, authority, accepted_policy_ids={"other-policy"})
            self.assertEqual(decision.status, "BLOCK")


if __name__ == "__main__":
    unittest.main()
