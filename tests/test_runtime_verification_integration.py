import unittest

from src.execution_identity import ExecutionIdentity
from src.live_operating_console import Command, LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge


class RuntimeVerificationIntegrationTests(unittest.TestCase):
    def test_live_runtime_attaches_verification_result(self):
        console = LiveOperatingConsole()
        command = Command(
            id="cmd-verify-1",
            objective="verify runtime",
            priority="P1",
            owner="operator",
            expected_output="runtime verified",
            status="INBOX",
            next_action="review",
        )
        console.add_command(command)
        identity = ExecutionIdentity(
            account_id="acct-1",
            instance_id="instance-1",
            environment_id="prod",
            session_id="session-1",
        )

        record = LiveRuntimeBridge(console).execute(
            command.id,
            execution_identity=identity,
        )

        self.assertIsNotNone(record.verification)
        self.assertTrue(record.verification.verified)
        self.assertEqual(record.verification.execution_id, record.operating_loop.execution_id)


if __name__ == "__main__":
    unittest.main()
