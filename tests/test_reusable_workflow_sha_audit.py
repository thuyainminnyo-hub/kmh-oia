#!/usr/bin/env python3
"""Unit tests for the reusable workflow SHA audit."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_reusable_workflow_refs import audit


class ReusableWorkflowAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / ".github" / "workflows"
        self.folder.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, uses=None):
        body = "name: fixture\non:\n  workflow_dispatch:\n"
        if uses is None:
            body += "jobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n"
        else:
            body += f"jobs:\n  call:\n    uses: {uses}\n"
        (self.folder / name).write_text(body, encoding="utf-8")

    def test_mutable_tag_fails(self):
        self.write("call.yml", "octo-org/shared/.github/workflows/ci.yml@v2")
        errors, scanned, checked = audit(self.root)
        self.assertEqual((scanned, checked), (1, 1))
        self.assertTrue(any("full 40-character SHA" in item for item in errors))

    def test_mutable_branch_fails(self):
        self.write("call.yml", "octo-org/shared/.github/workflows/ci.yml@main")
        errors, _, _ = audit(self.root)
        self.assertTrue(errors)

    def test_full_sha_passes(self):
        self.write("call.yml", "octo-org/shared/.github/workflows/ci.yml@0123456789abcdef0123456789abcdef01234567")
        errors, _, checked = audit(self.root)
        self.assertEqual(checked, 1)
        self.assertEqual(errors, [])

    def test_malformed_remote_reference_fails(self):
        self.write("call.yml", "octo-org/shared/workflows/ci.yml@0123456789abcdef0123456789abcdef01234567")
        errors, _, _ = audit(self.root)
        self.assertTrue(any("malformed" in item for item in errors))

    def test_existing_local_workflow_passes(self):
        (self.folder / "local.yml").write_text("name: local\njobs:\n  test:\n    runs-on: ubuntu-latest\n", encoding="utf-8")
        self.write("caller.yml", "./.github/workflows/local.yml")
        errors, _, checked = audit(self.root)
        self.assertEqual(checked, 1)
        self.assertEqual(errors, [])

    def test_missing_local_workflow_fails(self):
        self.write("caller.yml", "./.github/workflows/missing.yml")
        errors, _, _ = audit(self.root)
        self.assertTrue(any("does not exist" in item for item in errors))

    def test_no_reusable_workflow_calls_passes(self):
        self.write("ordinary.yml")
        errors, scanned, checked = audit(self.root)
        self.assertEqual((scanned, checked), (1, 0))
        self.assertEqual(errors, [])

    def test_multiline_uses_fails_closed(self):
        (self.folder / "call.yml").write_text(
            "name: fixture\njobs:\n  call:\n    uses:\n      owner/repo/.github/workflows/ci.yml@main\n",
            encoding="utf-8",
        )
        errors, _, checked = audit(self.root)
        self.assertEqual(checked, 1)
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
