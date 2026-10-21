"""Integration tests for source checkout verification inside release preflight."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.approval_policy import ApprovalRecord
from src.evidence_object import EvidenceObject
from src.pilot import run_pilot
from src.qa_gate import evaluate_evidence
from src.release_preflight import preflight_release
from src.release_envelope import create_envelope
from src.trusted_key_provider import InMemoryTrustedKeyProvider
from src.key_provider_signing import sign_decision_with_provider, require_provider_signed_release_allowed
from src.release_enforcer import ReleaseBlocked


class FakeApprovalAuthority:
    def __init__(self, record=None, authorized=True):
        self.record = record
        self.authorized = authorized

    def resolve_approval(self, approval_id):
        if self.record is None or self.record.approval_id != approval_id:
            return None
        return self.record

    def is_authorized_approver(self, approver_id, policy_id):
        return self.authorized


def init_repo(root: Path) -> str:
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "KMH release test"], check=True)
    (root / "app.py").write_text("controlled build\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "app.py"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "reviewed build"], check=True)
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


class ReleasePreflightTests(unittest.TestCase):
    def make_evidence(self, root, revision):
        _, evidence, _ = run_pilot(
            "preflight output",
            artifact_dir=root / "artifacts",
            evidence_path=root / "evidence.jsonl",
            session_id="preflight-test",
            source_revision=revision,
        )
        return evidence

    def authority_for(self, evidence, qa, revision, approver="human:reviewer"):
        return FakeApprovalAuthority(ApprovalRecord(
            approval_id="approval:preflight-001",
            approver_id=approver,
            evidence_id=evidence.evidence_id,
            qa_id=qa.qa_id,
            source_revision=revision,
            decision="APPROVE",
            policy_id="release-policy:v1",
            approved_at="2026-10-21T02:30:00Z",
        ))

    def test_clean_checkout_matching_evidence_and_approval_allows_signed_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            sha=init_repo(root)
            evidence=self.make_evidence(root.parent / f"{root.name}-pilot", sha)
            qa=evaluate_evidence(evidence, expected_output="preflight output")
            authority=self.authority_for(evidence, qa, sha)
            decision=preflight_release(
                evidence,qa,expected_source_revision=sha,checkout_root=root,
                approval_authority=authority,approval_id="approval:preflight-001",
                signing_service_id="service:signer",accepted_policy_ids={"release-policy:v1"},
            )
            self.assertEqual(decision.status,"ALLOW")
            key=b"test-key-for-preflight-signature-32-bytes-min"
            provider=InMemoryTrustedKeyProvider({"test-key":key},"test-key",{"test-key"})
            signed=sign_decision_with_provider(provider,decision)
            checked=require_provider_signed_release_allowed(provider,signed)
            self.assertEqual(checked.status,"ALLOW")

    def test_dirty_checkout_fails_before_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            sha=init_repo(root)
            (root / "app.py").write_text("changed after review\n",encoding="utf-8")
            evidence=self.make_evidence(root.parent / f"{root.name}-pilot",sha)
            qa=evaluate_evidence(evidence)
            authority=self.authority_for(evidence,qa,sha)
            with self.assertRaisesRegex(RuntimeError,"working tree"):
                preflight_release(evidence,qa,expected_source_revision=sha,checkout_root=root,
                    approval_authority=authority,approval_id="approval:preflight-001",
                    signing_service_id="service:signer",accepted_policy_ids={"release-policy:v1"})

    def test_checkout_revision_mismatch_fails_before_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            sha=init_repo(root)
            evidence=self.make_evidence(root.parent / f"{root.name}-pilot",sha)
            qa=evaluate_evidence(evidence)
            authority=self.authority_for(evidence,qa,sha)
            with self.assertRaisesRegex(RuntimeError,"does not match"):
                preflight_release(evidence,qa,expected_source_revision="0"*40,checkout_root=root,
                    approval_authority=authority,approval_id="approval:preflight-001",
                    signing_service_id="service:signer",accepted_policy_ids={"release-policy:v1"})

    def test_evidence_from_different_revision_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            sha=init_repo(root)
            evidence=self.make_evidence(root.parent / f"{root.name}-pilot", "1"*40)
            qa=evaluate_evidence(evidence)
            authority=self.authority_for(evidence,qa,sha)
            decision=preflight_release(evidence,qa,expected_source_revision=sha,checkout_root=root,
                approval_authority=authority,approval_id="approval:preflight-001",
                signing_service_id="service:signer",accepted_policy_ids={"release-policy:v1"})
            self.assertEqual(decision.status,"BLOCK")

    def test_missing_approval_blocks_and_cannot_be_signed_into_allow(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            sha=init_repo(root)
            evidence=self.make_evidence(root.parent / f"{root.name}-pilot",sha)
            qa=evaluate_evidence(evidence)
            decision=preflight_release(evidence,qa,expected_source_revision=sha,checkout_root=root,
                approval_authority=FakeApprovalAuthority(None),approval_id=None,
                signing_service_id="service:signer",accepted_policy_ids={"release-policy:v1"})
            self.assertEqual(decision.status,"BLOCK")
            provider=InMemoryTrustedKeyProvider({"test-key":b"test-key-for-preflight-signature-32-bytes-min"},"test-key",{"test-key"})
            signed=sign_decision_with_provider(provider,decision)
            with self.assertRaises(Exception):
                require_provider_signed_release_allowed(provider,signed)


if __name__=="__main__":
    unittest.main()
