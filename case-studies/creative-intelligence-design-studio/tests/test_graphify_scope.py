import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_graphify_scope import (
    POLICY_PATH,
    validate_graphify_scope,
)


def make_sandbox(project_root: Path) -> None:
    sandbox = project_root / "graphify-sandbox"
    (sandbox / "src").mkdir(parents=True)
    (sandbox / ".graphifyignore").write_text(
        "\n".join(
            [
                "**/.env",
                "**/.env.*",
                "**/*.pem",
                "**/*.key",
                "**/.ssh/**",
                "**/private/**",
                "**/learner-data/**",
                "**/raw-assets/**",
                "**/media/**",
                "**/graphify-out/**",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (sandbox / "src" / "contract_guard.py").write_text(
        "def approved(value):\n    return bool(value)\n",
        encoding="utf-8",
    )
    (sandbox / "src" / "outfit_flow.py").write_text(
        "from contract_guard import approved\n",
        encoding="utf-8",
    )


class GraphifyScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    def temporary_project(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        make_sandbox(root)
        return root

    def test_baseline_synthetic_scope_passes(self):
        root = self.temporary_project()
        self.assertEqual(validate_graphify_scope(copy.deepcopy(self.policy), root), [])

    def test_repository_wide_scan_root_is_rejected(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["scope"]["scan_root"] = "."
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("scan_root" in error for error in errors))

    def test_allowlist_cannot_be_widened(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["scope"]["allowed_paths"].append("../docs/")
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("allowed_paths" in error for error in errors))

    def test_install_and_indexing_must_remain_disabled(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["execution"]["index_allowed"] = True
        policy["execution"]["assistant_skill_install_allowed"] = True
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("index_allowed" in error for error in errors))
        self.assertTrue(any("assistant_skill_install_allowed" in error for error in errors))

    def test_model_backend_must_remain_disabled(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["execution"]["semantic_backend"] = "auto"
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("semantic_backend" in error for error in errors))

    def test_secret_file_is_rejected(self):
        root = self.temporary_project()
        (root / "graphify-sandbox" / ".env").write_text(
            "SYNTHETIC_TEST_VALUE=not-a-secret\n",
            encoding="utf-8",
        )
        errors = validate_graphify_scope(copy.deepcopy(self.policy), root)
        self.assertTrue(any("sensitive path" in error for error in errors))

    def test_non_python_asset_is_rejected(self):
        root = self.temporary_project()
        (root / "graphify-sandbox" / "src" / "portrait.png").write_bytes(b"synthetic")
        errors = validate_graphify_scope(copy.deepcopy(self.policy), root)
        self.assertTrue(any("allowlist" in error for error in errors))

    def test_symlink_is_rejected(self):
        root = self.temporary_project()
        link = root / "graphify-sandbox" / "src" / "external.py"
        target = root / "outside.py"
        target.write_text("def outside():\n    return True\n", encoding="utf-8")
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable in this environment")
        errors = validate_graphify_scope(copy.deepcopy(self.policy), root)
        self.assertTrue(any("symlink" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
