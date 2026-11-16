import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.verify_graphify_source import VerificationError, verify_source


class GraphifySourceVerificationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "qa@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Synthetic QA"], check=True)
        (self.root / "graphify").mkdir()
        (self.root / "pyproject.toml").write_text('[project]\nname = "graphifyy"\nversion = "0.9.100"\n', encoding="utf-8")
        (self.root / "graphify" / "cache.py").write_text("_AST_CACHE_SCHEMA = 33\n", encoding="utf-8")
        (self.root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
        self._commit_and_tag()

    def _git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True).strip()

    def _commit_and_tag(self):
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "synthetic source"], check=True)
        self.commit = self._git("rev-parse", "HEAD")
        self._git("tag", "-a", "-f", "v0.9.100", "-m", "synthetic release")
        self.lock_blob = self._git("rev-parse", "v0.9.100:uv.lock")

    def _commit_mutation_and_repin_fixture(self):
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "synthetic mutation fixture"], check=True)
        self.commit = self._git("rev-parse", "HEAD")
        subprocess.run(["git", "-C", str(self.root), "tag", "-f", "-a", "v0.9.100", "-m", "synthetic mutated release"], check=True)
        self.lock_blob = self._git("rev-parse", "v0.9.100:uv.lock")

    def _verify(self):
        return verify_source(self.root, expected_version="0.9.100", expected_commit=self.commit,
            expected_lock_blob=self.lock_blob, expected_schema=33, expected_tag="v0.9.100")

    def test_exact_pinned_source_passes(self):
        result = self._verify()
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["graphify_install_performed"])
        self.assertFalse(result["graphify_extraction_performed"])

    def test_dirty_worktree_fails_closed(self):
        (self.root / "graphify" / "cache.py").write_text("_AST_CACHE_SCHEMA = 34\\n", encoding="utf-8")
        with self.assertRaisesRegex(VerificationError, "source checkout is not clean"):
            self._verify()

    def test_wrong_commit_fails(self):
        with self.assertRaisesRegex(VerificationError, "source commit mismatch"):
            verify_source(self.root, expected_version="0.9.100", expected_commit="0" * 40,
                expected_lock_blob=self.lock_blob, expected_schema=33, expected_tag="v0.9.100")

    def test_tag_must_point_to_exact_commit(self):
        alternate = subprocess.check_output(
            ["git", "-C", str(self.root), "commit-tree", self._git("rev-parse", "HEAD^{tree}"), "-p", self.commit, "-m", "alternate tag target"],
            text=True,
        ).strip()
        subprocess.run(["git", "-C", str(self.root), "tag", "-f", "v0.9.100", alternate], check=True)
        with self.assertRaisesRegex(VerificationError, "tag target mismatch"):
            self._verify()

    def test_lock_blob_mismatch_fails(self):
        with self.assertRaisesRegex(VerificationError, "uv.lock blob mismatch"):
            verify_source(self.root, expected_version="0.9.100", expected_commit=self.commit,
                expected_lock_blob="0" * 40, expected_schema=33, expected_tag="v0.9.100")

    def test_package_version_mismatch_fails(self):
        (self.root / "pyproject.toml").write_text('[project]\nname = "graphifyy"\nversion = "0.9.101"\n', encoding="utf-8")
        self._commit_mutation_and_repin_fixture()
        with self.assertRaisesRegex(VerificationError, "package version mismatch"):
            self._verify()

    def test_missing_schema_fails_closed(self):
        (self.root / "graphify" / "cache.py").write_text("OTHER_CONSTANT = 33\n", encoding="utf-8")
        self._commit_mutation_and_repin_fixture()
        with self.assertRaisesRegex(VerificationError, "exactly one literal"):
            self._verify()

    def test_duplicate_schema_assignment_fails_closed(self):
        (self.root / "graphify" / "cache.py").write_text("_AST_CACHE_SCHEMA = 33\n_AST_CACHE_SCHEMA = 33\n", encoding="utf-8")
        self._commit_mutation_and_repin_fixture()
        with self.assertRaisesRegex(VerificationError, "exactly one literal"):
            self._verify()


if __name__ == "__main__":
    unittest.main()
