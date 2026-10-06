import unittest
from src.execution_identity import ExecutionIdentity
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge

class ExecutionIdentityRuntimeTests(unittest.TestCase):
    def test_identity_is_carried_into_execution_record(self):
        console = LiveOperatingConsole(date="2026-10-06", primary_objective="identity")
        command = console.add_command(objective="run", priority="P1", owner="owner", expected_output="done")
        bridge = LiveRuntimeBridge(console)
        identity = ExecutionIdentity("account-a", "instance-1", "prod", "session-1")
        record = bridge.execute(command.id, execution_identity=identity)
        self.assertIsNotNone(record.execution_identity)
        self.assertEqual(record.execution_identity.identity.key, "account-a:instance-1:prod:session-1")
        self.assertEqual(record.execution_identity.command_id, command.id)
        self.assertEqual(record.execution_identity.execution_id, record.operating_loop.execution_id)

if __name__ == "__main__":
    unittest.main()
