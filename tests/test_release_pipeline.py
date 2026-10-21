"""End-to-end test of source preflight, approval, signing and protected execution."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.approval_policy import ApprovalRecord
from src.pilot import run_pilot
from src.protected_action import ProtectedActionBlocked
from src.qa_gate import evaluate_evidence
from src.release_pipeline import execute_release_pipeline
from src.trusted_key_provider import InMemoryTrustedKeyProvider


KEY = b"kmh-oia-release-pipeline-integration-key-minimum-32-bytes"


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
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Release pipeline test"], check=True)
    (root / "release.py").write_text("reviewed release\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "release.py"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "reviewed release"], check=True)
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


class ReleasePipelineTests(unittest.TestCase):
    def prepare(self, outer: Path, checkout: Path, sha: str, approved=True, approver="human:approver"):
        evidence_root = outer / "evidence"
        _, evidence, _ = run_pilot(
            "end-to-end release output",
            artifact_dir=evidence_root / "artifacts",
            evidence_path=evidence_root / "evidence.jsonl",
            session_id="release-pipeline-e2e",
            source_revision=sha,
        )
        qa = evaluate_evidence(evidence, expected_output="end-to-end release output")
        record = None
        if approved:
            record = ApprovalRecord(
                approval_id="approval:pipeline-001",
                approver_id=approver,
                evidence_id=evidence.evidence_id,
                qa_id=qa.qa_id,
                source_revision=sha,
                decision="APPROVE",
                policy_id="release-policy:v1",
                approved_at="2026-10-21T03:00:00Z",
            )
        authority = FakeApprovalAuthority(record, authorized=True)
        provider = InMemoryTrustedKeyProvider(
            {"pipeline-key": KEY}, "pipeline-key", {"pipeline-key"}
        )
        return evidence, qa, authority, provider

    def run_pipeline(self, evidence, qa, authority, provider, root, sha, callback, approval_id="approval:pipeline-001"):
        return execute_release_pipeline(
            evidence,
            qa,
            expected_source_revision=sha,
            checkout_root=root,
            approval_authority=authority,
            approval_id=approval_id,
            signing_service_id="service:release-signer",
            accepted_policy_ids={"release-policy:v1"},
            key_provider=provider,
            protected_action=callback,
        )

    def test_clean_checkout_and_approved_evidence_runs_action_once(self):
        with tempfile.TemporaryDirectory() as outer_dir, tempfile.TemporaryDirectory() as checkout_dir:
            outer, checkout = Path(outer_dir), Path(checkout_dir)
            sha = init_repo(checkout)
            evidence, qa, authority, provider = self.prepare(outer, checkout, sha)
            calls = []
            decision, signed, result = self.run_pipeline(
                evidence, qa, authority, provider, checkout, sha,
                lambda: calls.append("executed") or "deployed",
            )
            self.assertEqual(decision.status, "ALLOW")
            self.assertEqual(signed.key_id, "pipeline-key")
            self.assertEqual(result, "deployed")
            self.assertEqual(calls, ["executed"])

    def test_missing_approval_blocks_without_invoking_action(self):
        with tempfile.TemporaryDirectory() as outer_dir, tempfile.TemporaryDirectory() as checkout_dir:
            outer, checkout = Path(outer_dir), Path(checkout_dir)
            sha = init_repo(checkout)
            evidence, qa, authority, provider = self.prepare(outer, checkout, sha, approved=False)
            calls = []
            with self.assertRaises(ProtectedActionBlocked):
                self.run_pipeline(evidence, qa, authority, provider, checkout, sha,
                                  lambda: calls.append("executed"))
            self.assertEqual(calls, [])

    def test_wrong_expected_revision_blocks_before_action(self):
        with tempfile.TemporaryDirectory() as outer_dir, tempfile.TemporaryDirectory() as checkout_dir:
            outer, checkout = Path(outer_dir), Path(checkout_dir)
            sha = init_repo(checkout)
            evidence, qa, authority, provider = self.prepare(outer, checkout, sha)
            calls = []
            with self.assertRaisesRegex(RuntimeError, "does not match"):
                self.run_pipeline(evidence, qa, authority, provider, checkout, "0" * 40,
                                  lambda: calls.append("executed"))
            self.assertEqual(calls, [])

    def test_dirty_checkout_blocks_before_action(self):
        with tempfile.TemporaryDirectory() as outer_dir, tempfile.TemporaryDirectory() as checkout_dir:
            outer, checkout = Path(outer_dir), Path(checkout_dir)
            sha = init_repo(checkout)
            evidence, qa, authority, provider = self.prepare(outer, checkout, sha)
            (checkout / "release.py").write_text("changed after review\n", encoding="utf-8")
            calls = []
            with self.assertRaisesRegex(RuntimeError, "working tree"):
                self.run_pipeline(evidence, qa, authority, provider, checkout, sha,
                                  lambda: calls.append("executed"))
            self.assertEqual(calls, [])

    def test_evidence_revision_mismatch_blocks_without_action(self):
        with tempfile.TemporaryDirectory() as outer_dir, tempfile.TemporaryDirectory() as checkout_dir:
            outer, checkout = Path(outer_dir), Path(checkout_dir)
            sha = init_repo(checkout)
            evidence, qa, authority, provider = self.prepare(outer, checkout, "1" * 40)
            calls = []
            with self.assertRaises(ProtectedActionBlocked):
                self.run_pipeline(evidence, qa, authority, provider, checkout, sha,
                                  lambda: calls.append("executed"))
            self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
