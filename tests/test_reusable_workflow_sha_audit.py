#!/usr/bin/env python3
"""Structural and adversarial tests for the reusable workflow SHA audit."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_reusable_workflow_refs import audit


VALID_SHA = "0123456789abcdef0123456789abcdef01234567"


class ReusableWorkflowAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / ".github" / "workflows"
        self.folder.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, content):
        (self.folder / name).write_text(content, encoding="utf-8")

    def call(self, reference):
        return (
            "name: fixture\non:\n  workflow_dispatch:\n"
            "jobs:\n  call:\n    uses: " + reference + "\n"
        )

    def test_mutable_tag_fails(self):
        self.write("call.yml", self.call("octo-org/shared/.github/workflows/ci.yml@v2"))
        errors, scanned, checked, refs = audit(self.root)
        self.assertEqual((scanned, checked, refs), (1, 1, []))
        self.assertTrue(any("full 40-character commit SHA" in item for item in errors))

    def test_mutable_branch_fails(self):
        self.write("call.yml", self.call("octo-org/shared/.github/workflows/ci.yml@main"))
        errors, _, _, _ = audit(self.root)
        self.assertTrue(errors)

    def test_full_sha_passes(self):
        self.write("call.yml", self.call(f"octo-org/shared/.github/workflows/ci.yml@{VALID_SHA}"))
        errors, _, checked, refs = audit(self.root)
        self.assertEqual(checked, 1)
        self.assertEqual(errors, [])
        self.assertEqual(refs[0]["kind"], "remote")

    def test_malformed_remote_reference_fails(self):
        self.write("call.yml", self.call(f"octo-org/shared/workflows/ci.yml@{VALID_SHA}"))
        errors, _, _, _ = audit(self.root)
        self.assertTrue(any("malformed" in item for item in errors))

    def test_existing_local_workflow_passes(self):
        self.write("local.yml", "name: local\non:\n  workflow_dispatch:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
        self.write("caller.yml", self.call("./.github/workflows/local.yml"))
        errors, _, checked, refs = audit(self.root)
        self.assertEqual(checked, 1)
        self.assertEqual(errors, [])
        self.assertEqual(refs[0]["kind"], "local")

    def test_dollar_local_workflow_passes(self):
        self.write("local.yml", "name: local\non:\n  workflow_dispatch:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
        self.write("caller.yml", self.call("$/.github/workflows/local.yml"))
        errors, _, _, refs = audit(self.root)
        self.assertEqual(errors, [])
        self.assertEqual(refs[0]["kind"], "local")

    def test_missing_local_workflow_fails(self):
        self.write("caller.yml", self.call("./.github/workflows/missing.yml"))
        errors, _, _, _ = audit(self.root)
        self.assertTrue(any("does not exist" in item for item in errors))

    def test_local_path_traversal_fails(self):
        self.write("caller.yml", self.call("./.github/workflows/../../outside.yml"))
        errors, _, _, _ = audit(self.root)
        self.assertTrue(any("escapes" in item for item in errors))

    def test_no_reusable_workflow_calls_passes(self):
        self.write("ordinary.yml", (
            "name: ordinary\non:\n  workflow_dispatch:\njobs:\n"
            "  test:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - uses: actions/checkout@v4\n"
        ))
        errors, scanned, checked, refs = audit(self.root)
        self.assertEqual((scanned, checked, refs), (1, 0, []))
        self.assertEqual(errors, [])

    def test_step_level_uses_is_not_misclassified(self):
        self.write("ordinary.yml", (
            "name: ordinary\non:\n  workflow_dispatch:\njobs:\n"
            "  test:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - name: checkout\n        uses: actions/checkout@v4\n"
        ))
        errors, _, checked, _ = audit(self.root)
        self.assertEqual(checked, 0)
        self.assertEqual(errors, [])

    def test_block_scalar_text_is_not_misclassified(self):
        self.write("ordinary.yml", (
            "name: ordinary\non:\n  workflow_dispatch:\njobs:\n"
            "  test:\n    runs-on: ubuntu-latest\n"
            "    steps:\n      - run: |\n"
            "          jobs:\n          call:\n"
            "            uses: octo-org/shared/.github/workflows/ci.yml@main\n"
        ))
        errors, _, checked, _ = audit(self.root)
        self.assertEqual(checked, 0)
        self.assertEqual(errors, [])

    def test_duplicate_mapping_key_fails(self):
        self.write("duplicate.yml", (
            "name: duplicate\non:\n  workflow_dispatch:\njobs:\n"
            "  test:\n    runs-on: ubuntu-latest\n"
            "  test:\n    uses: octo-org/shared/.github/workflows/ci.yml@main\n"
        ))
        errors, _, _, _ = audit(self.root)
        self.assertTrue(any("duplicate mapping key" in item for item in errors))

    def test_malformed_yaml_fails(self):
        self.write("broken.yml", "name: broken\njobs: [\n")
        errors, _, _, _ = audit(self.root)
        self.assertTrue(any("YAML parse/structure error" in item for item in errors))

    def test_github_custom_yaml_tag_is_treated_as_data(self):
        self.write("tagged.yml", (
            "name: tagged\non:\n  workflow_dispatch:\njobs:\n"
            "  test:\n    runs-on: ubuntu-latest\n"
            "    if: !cancelled()\n"
        ))
        errors, _, _, _ = audit(self.root)
        self.assertEqual(errors, [])

    def test_missing_jobs_mapping_fails_closed(self):
        self.write("missing-jobs.yml", "name: no-jobs\non:\n  workflow_dispatch:\n")
        errors, _, _, _ = audit(self.root)
        self.assertTrue(any("'jobs' must be a YAML mapping" in item for item in errors))

    def test_no_workflow_files_fails_closed(self):
        errors, scanned, checked, refs = audit(self.root)
        self.assertEqual((scanned, checked, refs), (0, 0, []))
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
