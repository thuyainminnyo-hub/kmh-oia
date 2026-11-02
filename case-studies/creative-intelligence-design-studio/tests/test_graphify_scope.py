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

    def test_candidate_release_is_exactly_reviewed_v0_9_100(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["candidate_version"] = "latest"
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("candidate Graphify version" in error for error in errors))

    def test_release_commit_must_match_verified_tag(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["release_commit_sha"] = "deadbeef"
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("candidate source commit" in error for error in errors))

    def test_unverified_or_missing_wheel_checksum_fails(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["pypi_wheel_sha256"] = "not-a-checksum"
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("pypi_wheel_sha256" in error for error in errors))

    def test_owner_install_approval_must_remain_pending(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["owner_install_approval"] = "approved"
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("owner_install_approval" in error for error in errors))

    def test_optional_extras_must_remain_disabled(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["optional_extras_enabled"] = ["pdf", "video", "openai"]
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("optional_extras_enabled" in error for error in errors))

    def test_passed_runtime_dependency_audit_requires_evidence(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["runtime_dependency_audit"]["status"] = "passed"
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("passed runtime dependency audit requires evidence" in error for error in errors))

    def test_passed_runtime_dependency_audit_accepts_exact_ci_evidence(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        audit = policy["source_intake"]["runtime_dependency_audit"]
        audit["status"] = "passed"
        audit["evidence"] = {
            "run_id": 41422855820,
            "commit_sha": "0a4643362e92b6d7b252008a2a3ae586740ec9b2",
            "artifact_id": 13129673852,
            "uv_version": "0.13.6",
            "pip_audit_version": "2.10.1",
            "pypi_exit_code": 0,
            "osv_exit_code": 0,
            "pypi_result": "no_known_vulnerabilities_found",
            "osv_result": "no_known_vulnerabilities_found",
            "requirements_hashes": "present_and_required",
            "pypi_hash_verification": "passed",
            "osv_hash_verification": "presence_only",
        }
        self.assertEqual(validate_graphify_scope(policy, root), [])

    def test_passed_runtime_dependency_audit_rejects_modified_evidence(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        audit = policy["source_intake"]["runtime_dependency_audit"]
        audit["status"] = "passed"
        audit["evidence"] = {"run_id": 1}
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("evidence mismatch" in error for error in errors))

    def test_dependency_audit_tool_must_be_exactly_pinned(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["runtime_dependency_audit"]["tool_version"] = "latest"
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("pinned to pip-audit 2.10.1" in error for error in errors))

    def test_dependency_audit_uv_version_must_be_exactly_pinned(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["runtime_dependency_audit"]["uv_version"] = "latest"
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("uv version must remain pinned to 0.13.6" in error for error in errors))

    def test_dependency_audit_must_use_frozen_upstream_lock_mode(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["runtime_dependency_audit"]["lock_mode"] = "locked"
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("frozen lock mode" in error for error in errors))

    def test_dependency_audit_strict_mode_is_required(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["runtime_dependency_audit"]["strict_mode_required"] = False
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("--strict" in error for error in errors))

    def test_dependency_audit_hash_verification_is_required(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["runtime_dependency_audit"]["hashes_required"] = False
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("hash-checked requirements" in error for error in errors))

    def test_dependency_audit_requires_both_vulnerability_services(self):
        root = self.temporary_project()
        policy = copy.deepcopy(self.policy)
        policy["source_intake"]["runtime_dependency_audit"]["services"] = ["pypi"]
        errors = validate_graphify_scope(policy, root)
        self.assertTrue(any("both PyPI and OSV" in error for error in errors))

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
