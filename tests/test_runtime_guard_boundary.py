import unittest

from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge


class RuntimeGuardBoundaryTests(unittest.TestCase):
    def _command(self, console):
        return console.add_command(
            objective="guarded operation",
            priority="P1",
            owner="security",
            expected_output="result",
            source_action_kind="cybersecurity_remediation",
        )

    def test_guard_is_required_before_runtime_execution(self):
        calls = []

        class RuntimeSpy:
            def execute_detailed(self, *args, **kwargs):
                calls.append(True)
                return ("response", [], [])

        console = LiveOperatingConsole(date="2026-10-27")
        command = self._command(console)
        bridge = LiveRuntimeBridge(console, runtime=RuntimeSpy())

        with self.assertRaises(PermissionError):
            bridge.execute(command.id)

        self.assertEqual(calls, [])
        self.assertEqual(command.status, "INBOX")

    def test_authorized_guard_still_cannot_fall_through_to_generic_runtime(self):
        calls = []

        class RuntimeSpy:
            def execute_detailed(self, *args, **kwargs):
                calls.append(True)
                return ("response", [], [])

        console = LiveOperatingConsole(date="2026-10-27")
        command = self._command(console)
        bridge = LiveRuntimeBridge(
            console,
            runtime=RuntimeSpy(),
            cybersecurity_execution_guard=lambda _command: (True, "approved"),
        )

        with self.assertRaisesRegex(PermissionError, "dedicated asset-scoped remediation executor"):
            bridge.execute(command.id)

        self.assertEqual(calls, [])
        self.assertEqual(command.status, "INBOX")

    def test_denied_guard_never_calls_runtime(self):
        calls = []

        class RuntimeSpy:
            def execute_detailed(self, *args, **kwargs):
                calls.append(True)
                return ("response", [], [])

        console = LiveOperatingConsole(date="2026-10-27")
        command = self._command(console)
        bridge = LiveRuntimeBridge(
            console,
            runtime=RuntimeSpy(),
            cybersecurity_execution_guard=lambda _command: (False, "approval missing"),
        )

        with self.assertRaisesRegex(PermissionError, "approval missing"):
            bridge.execute(command.id)

        self.assertEqual(calls, [])
        self.assertEqual(command.status, "INBOX")


if __name__ == "__main__":
    unittest.main()
