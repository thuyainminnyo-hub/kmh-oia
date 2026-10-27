import copy
import json
import tempfile
import unittest
from pathlib import Path

from src.cybersecurity_runtime_guard import build_registry_execution_guard
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from scripts.cybersecurity_registry import save_version

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/fixtures/cybersecurity/valid-pending-record.json").read_text(encoding="utf-8"))


class RegistryRuntimeGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "registry.jsonl"
        self.record = copy.deepcopy(FIXTURE)
        save_version(self.path, self.record, stored_at="2026-10-27T00:00:00+00:00")
        self.console = LiveOperatingConsole(date="2026-10-27")
        self.command = self.console.add_command(
            objective="guarded operation", priority="P1", owner="security",
            expected_output="result", source_action_kind="cybersecurity_remediation",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_registry_guard_blocks_live_runtime_before_side_effect(self):
        calls = []
        class RuntimeSpy:
            def execute_detailed(self, *args, **kwargs):
                calls.append(True)
                return ("unexpected", [], [])

        guard = build_registry_execution_guard(
            self.path, lambda _command: (self.record["case_id"], 1, "remediate"),
        )
        bridge = LiveRuntimeBridge(self.console, runtime=RuntimeSpy(), cybersecurity_execution_guard=guard)
        with self.assertRaisesRegex(PermissionError, "cybersecurity execution blocked"):
            bridge.execute(self.command.id)
        self.assertEqual(calls, [])
        self.assertEqual(self.command.status, "INBOX")

    def test_pending_registry_record_is_denied(self):
        guard = build_registry_execution_guard(
            self.path, lambda _command: (self.record["case_id"], 1, "remediate"),
        )
        allowed, reason = guard(self.command)
        self.assertFalse(allowed)
        self.assertTrue(reason)

    def test_unknown_version_is_denied(self):
        guard = build_registry_execution_guard(
            self.path, lambda _command: (self.record["case_id"], 99, "remediate"),
        )
        allowed, reason = guard(self.command)
        self.assertFalse(allowed)
        self.assertIn("not found", reason)

    def test_corrupt_registry_fails_closed(self):
        self.path.write_text("{bad json}\n", encoding="utf-8")
        guard = build_registry_execution_guard(
            self.path, lambda _command: (self.record["case_id"], 1, "remediate"),
        )
        allowed, reason = guard(self.command)
        self.assertFalse(allowed)
        self.assertIn("failed closed", reason)


if __name__ == "__main__":
    unittest.main()
