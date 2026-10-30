#!/usr/bin/env python3
"""Tests for repository-wide GitHub Actions dependency assurance."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_action_dependencies import audit

SHA = "0123456789abcdef0123456789abcdef01234567"
DIGEST = "sha256:" + "a" * 64


class ActionDependencyAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workflows = self.root / ".github" / "workflows"
        self.workflows.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def workflow(self, steps="", extra=""):
        return (
            "name: fixture\non:\n  workflow_dispatch:\njobs:\n"
            "  test:\n    runs-on: ubuntu-latest\n"
            + extra + ("    steps:\n" + steps if steps else "    steps: []\n")
        )

    def write_workflow(self, content):
        (self.workflows / "test.yml").write_text(content, encoding="utf-8")

    def test_full_sha_action_passes(self):
        self.write_workflow(self.workflow(f"      - uses: actions/checkout@{SHA}\n"))
        result = audit(self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["action_uses_checked"], 1)

    def test_mutable_action_tag_creates_hold(self):
        self.write_workflow(self.workflow("      - uses: actions/checkout@v4\n"))
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(any("full 40-character commit SHA" in f["message"] for f in result["findings"]))

    def test_local_composite_and_nested_action_are_scanned(self):
        action = self.root / ".github" / "actions" / "outer"
        action.mkdir(parents=True)
        (action / "action.yml").write_text(
            "name: outer\ndescription: fixture\nruns:\n  using: composite\n"
            "  steps:\n    - uses: actions/checkout@" + SHA + "\n",
            encoding="utf-8",
        )
        self.write_workflow(self.workflow("      - uses: $/.github/actions/outer\n"))
        result = audit(self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["composite_action_manifests_scanned"], 1)
        self.assertEqual(result["action_uses_checked"], 2)

    def test_missing_local_manifest_creates_hold(self):
        self.write_workflow(self.workflow("      - uses: ./.github/actions/missing\n"))
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(any("manifest" in f["message"] for f in result["findings"]))

    def test_local_path_traversal_creates_hold(self):
        self.write_workflow(self.workflow("      - uses: $/../../outside\n"))
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(any("escapes repository root" in f["message"] for f in result["findings"]))

    def test_docker_step_requires_digest(self):
        self.write_workflow(self.workflow("      - uses: docker://alpine:3.20\n"))
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(any("sha256 digest" in f["message"] for f in result["findings"]))

    def test_docker_step_with_digest_passes(self):
        self.write_workflow(self.workflow("      - uses: docker://alpine@" + DIGEST + "\n"))
        result = audit(self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["container_references_checked"], 1)

    def test_job_container_requires_digest(self):
        self.write_workflow(self.workflow("", extra="    container:\n      image: python:3.12\n"))
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["container_references_checked"], 1)

    def test_job_container_with_digest_passes(self):
        self.write_workflow(self.workflow("", extra="    container:\n      image: python@" + DIGEST + "\n"))
        result = audit(self.root)
        self.assertEqual(result["status"], "PASS")

    def test_expression_action_reference_creates_hold(self):
        self.write_workflow(self.workflow('      - uses: ${{ inputs.action }}\n'))
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")

    def test_duplicate_yaml_key_is_parse_error(self):
        self.write_workflow("name: bad\njobs:\n  test:\n    runs-on: ubuntu-latest\n  test:\n    steps: []\n")
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(result["errors"])

    def test_step_level_uses_not_reusable_workflow_uses(self):
        self.write_workflow(self.workflow(f"      - uses: actions/checkout@{SHA}\n"))
        result = audit(self.root)
        self.assertFalse(any("reusable workflow" in f["message"] for f in result["findings"]))


if __name__ == "__main__":
    unittest.main()
