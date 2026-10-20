import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.capture_target_host_evidence import capture_target_evidence


VALID_SHA = "a" * 40


class TargetHostEvidenceCaptureTests(unittest.TestCase):
    def _repo(self, root: Path, sha: str = VALID_SHA) -> Path:
        git_dir = root / ".git"
        git_dir.mkdir()
        return root

    def test_captures_complete_receipt_after_passing_smoke_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "evidence.sqlite3"
            db_path.write_text("fixture", encoding="utf-8")
            with patch("scripts.capture_target_host_evidence.resolve_checkout_sha", return_value=VALID_SHA), patch(
                "scripts.capture_target_host_evidence.smoke_test",
                return_value={
                    "schema_version": "1.0",
                    "test": "sqlite_replay_across_independent_os_processes",
                    "db_path": str(db_path),
                    "first_process": {"healthy": True, "accepted": True, "reason": "accepted"},
                    "second_process": {"healthy": True, "accepted": False, "reason": "replay_detected"},
                    "result": "PASS",
                },
            ):
                result = capture_target_evidence(
                    db_path=db_path,
                    environment_id="staging",
                    host_or_service_id="host-1",
                    persistent_volume_confirmed=True,
                    expected_commit_sha=VALID_SHA,
                    repo_root=root,
                )
            self.assertEqual(result["commit_sha"], VALID_SHA)
            self.assertEqual(result["database_path"], str(db_path))
            self.assertEqual(result["smoke_test_report"]["db_path"], str(db_path))
            self.assertTrue(result["smoke_tested_at_utc"].endswith("Z"))
            self.assertIs(result["persistent_volume_confirmed"], True)
            self.assertEqual(result["smoke_test_report"]["result"], "PASS")
            self.assertEqual(result["capture_schema_version"], "1.0")

    def test_requires_explicit_volume_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "Persistent-volume confirmation"):
                capture_target_evidence(
                    db_path=root / "db.sqlite3",
                    environment_id="staging",
                    host_or_service_id="host-1",
                    persistent_volume_confirmed=False,
                    expected_commit_sha=VALID_SHA,
                    repo_root=root,
                )

    def test_expected_sha_must_match_exact_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("scripts.capture_target_host_evidence.resolve_checkout_sha", return_value="b" * 40):
                with self.assertRaisesRegex(ValueError, "Checkout SHA mismatch"):
                    capture_target_evidence(
                        db_path=root / "db.sqlite3",
                        environment_id="staging",
                        host_or_service_id="host-1",
                        persistent_volume_confirmed=True,
                        expected_commit_sha=VALID_SHA,
                        repo_root=root,
                    )

    def test_missing_identifiers_are_rejected_before_running_smoke_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("scripts.capture_target_host_evidence.resolve_checkout_sha", return_value=VALID_SHA), patch(
                "scripts.capture_target_host_evidence.smoke_test"
            ) as smoke:
                with self.assertRaisesRegex(ValueError, "environment_id"):
                    capture_target_evidence(
                        db_path=root / "db.sqlite3",
                        environment_id=" ",
                        host_or_service_id="host-1",
                        persistent_volume_confirmed=True,
                        expected_commit_sha=VALID_SHA,
                        repo_root=root,
                    )
                smoke.assert_not_called()

    def test_rejects_smoke_report_for_different_database_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "expected.sqlite3"
            with patch("scripts.capture_target_host_evidence.resolve_checkout_sha", return_value=VALID_SHA), patch(
                "scripts.capture_target_host_evidence.smoke_test",
                return_value={
                    "result": "PASS",
                    "test": "sqlite_replay_across_independent_os_processes",
                    "db_path": str(root / "different.sqlite3"),
                },
            ):
                with self.assertRaisesRegex(RuntimeError, "database path"):
                    capture_target_evidence(
                        db_path=db_path,
                        environment_id="staging",
                        host_or_service_id="host-1",
                        persistent_volume_confirmed=True,
                        expected_commit_sha=VALID_SHA,
                        repo_root=root,
                    )

    def test_rejects_smoke_report_for_unexpected_test_identifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "expected.sqlite3"
            with patch("scripts.capture_target_host_evidence.resolve_checkout_sha", return_value=VALID_SHA), patch(
                "scripts.capture_target_host_evidence.smoke_test",
                return_value={
                    "result": "PASS",
                    "test": "fake-pass",
                    "db_path": str(db_path),
                },
            ):
                with self.assertRaisesRegex(RuntimeError, "unexpected test identifier"):
                    capture_target_evidence(
                        db_path=db_path,
                        environment_id="staging",
                        host_or_service_id="host-1",
                        persistent_volume_confirmed=True,
                        expected_commit_sha=VALID_SHA,
                        repo_root=root,
                    )

    def test_smoke_failure_never_returns_pass_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("scripts.capture_target_host_evidence.resolve_checkout_sha", return_value=VALID_SHA), patch(
                "scripts.capture_target_host_evidence.smoke_test",
                return_value={"result": "FAIL"},
            ):
                with self.assertRaisesRegex(RuntimeError, "did not pass"):
                    capture_target_evidence(
                        db_path=root / "db.sqlite3",
                        environment_id="staging",
                        host_or_service_id="host-1",
                        persistent_volume_confirmed=True,
                        expected_commit_sha=VALID_SHA,
                        repo_root=root,
                    )


if __name__ == "__main__":
    unittest.main()
