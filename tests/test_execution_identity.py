import unittest
from src.execution_identity import ExecutionIdentity, ExecutionIdentityContext

class ExecutionIdentityTests(unittest.TestCase):
    def test_identity_builds_canonical_collision_resistant_key(self):
        identity=ExecutionIdentity("account-a","instance-1","prod","session-9")
        self.assertTrue(identity.key.startswith("sha256:"))
        self.assertEqual(identity.provenance()["instance_id"],"instance-1")
        self.assertNotEqual(ExecutionIdentity("a:b","c","d","e").key,ExecutionIdentity("a","b:c","d","e").key)
    def test_identity_requires_all_scopes(self):
        with self.assertRaises(ValueError): ExecutionIdentity("account-a","","prod","session-9")
    def test_context_links_command_and_execution(self):
        context=ExecutionIdentityContext(ExecutionIdentity("a","i","p","s"),"cmd-1","exec-1")
        self.assertEqual(context.command_id,"cmd-1")
    def test_context_rejects_blank_identifiers(self):
        with self.assertRaises(ValueError): ExecutionIdentityContext(ExecutionIdentity("a","i","p","s")," ","e")
if __name__=="__main__": unittest.main()
