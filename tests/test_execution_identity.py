import unittest
from src.execution_identity import ExecutionIdentity, ExecutionIdentityContext

class ExecutionIdentityTests(unittest.TestCase):
    def test_identity_builds_stable_hierarchy_key(self):
        identity = ExecutionIdentity("account-a", "instance-1", "prod", "session-9")
        self.assertEqual(identity.key, "account-a:instance-1:prod:session-9")
        self.assertEqual(identity.provenance()["instance_id"], "instance-1")
        self.assertEqual(identity.provenance()["account_id"], "account-a")

    def test_identity_requires_all_scopes(self):
        with self.assertRaises(ValueError):
            ExecutionIdentity("account-a", "", "prod", "session-9")

    def test_context_links_command_and_execution(self):
        identity = ExecutionIdentity("account-a", "instance-1", "prod", "session-9")
        context = ExecutionIdentityContext(identity, "cmd-1", "exec-1")
        self.assertEqual(context.command_id, "cmd-1")
        self.assertEqual(context.execution_id, "exec-1")

if __name__ == "__main__":
    unittest.main()
