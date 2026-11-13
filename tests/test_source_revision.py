"""Tests for actual source-revision discovery from a Git checkout."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.source_revision import (
    discover_git_revision,
    require_verified_source_revision,
    verify_source_revision,
)


class SourceRevisionTests(unittest.TestCase):
    def init_repo(self, root: Path) -> str:
        subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "KMH OIA test"], check=True)
        (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "initial"], check=True)
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    def test_actual_revision_matches_clean_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = self.init_repo(root)
            self.assertEqual(discover_git_revision(root), expected)
            result = verify_source_revision(expected, root)
            self.assertTrue(result.matches)
            self.assertTrue(result.working_tree_clean)
            self.assertEqual(require_verified_source_revision(expected, root), expected)

    def test_revision_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repo(root)
            result = verify_source_revision("0" * 40, root)
            self.assertFalse(result.matches)
            with self.assertRaisesRegex(RuntimeError, "does not match"):
                require_verified_source_revision("0" * 40, root)

    def test_dirty_tracked_or_untracked_tree_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = self.init_repo(root)
            (root / "tracked.txt").write_text("modified\n", encoding="utf-8")
            result = verify_source_revision(expected, root)
            self.assertTrue(result.matches)
            self.assertFalse(result.working_tree_clean)
            with self.assertRaisesRegex(RuntimeError, "modified or untracked"):
                require_verified_source_revision(expected, root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = self.init_repo(root)
            (root / "new.txt").write_text("untracked\n", encoding="utf-8")
            self.assertFalse(verify_source_revision(expected, root).working_tree_clean)

    def test_invalid_expected_sha_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repo(root)
            result = verify_source_revision("main", root)
            self.assertFalse(result.matches)
            with self.assertRaisesRegex(RuntimeError, "full 40-character"):
                require_verified_source_revision("main", root)

    def test_non_git_directory_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = verify_source_revision("a" * 40, root)
            self.assertFalse(result.matches)
            self.assertFalse(result.working_tree_clean)


if __name__ == "__main__":
    unittest.main()
