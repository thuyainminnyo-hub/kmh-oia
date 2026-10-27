"""CLI contract tests for cybersecurity registry operations."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "cybersecurity_registry_cli.py"
FIXTURE = ROOT / "tests" / "fixtures" / "cybersecurity" / "valid-pending-record.json"


class CybersecurityRegistryCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.registry = self.root / "registry.jsonl"
        self.record = self.root / "record.json"
        self.record.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(CLI), *map(str, args)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )

    def test_append_verify_and_latest(self):
        appended = self.run_cli("append", "--record", self.record, "--registry", self.registry)
        self.assertEqual(appended.returncode, 0, appended.stderr)
        self.assertEqual(json.loads(appended.stdout)["version"], 1)

        verified = self.run_cli("verify", "--registry", self.registry)
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertEqual(json.loads(verified.stdout)["verified_entries"], 1)

        latest = self.run_cli("latest", "--registry", self.registry, "--case-id", "KMH-OIA-CYBER-2026-001")
        self.assertEqual(latest.returncode, 0, latest.stderr)
        self.assertEqual(json.loads(latest.stdout)["version"], 1)

    def test_latest_returns_nonzero_when_case_is_missing(self):
        result = self.run_cli("latest", "--registry", self.registry, "--case-id", "missing-case")
        self.assertEqual(result.returncode, 1)

    def test_authorize_fails_closed_for_pending_record(self):
        result = self.run_cli(
            "authorize", "--record", self.record, "--action", "remediate",
            "--now", "2026-10-27T00:00:00Z",
        )
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["allowed"])

    def test_append_rejects_invalid_record(self):
        record = json.loads(self.record.read_text(encoding="utf-8"))
        record["assessment"]["decision"] = "remediate"
        self.record.write_text(json.dumps(record), encoding="utf-8")
        result = self.run_cli("append", "--record", self.record, "--registry", self.registry)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.registry.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
