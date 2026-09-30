import unittest

from src.security import SecurityPolicy, ToolDecision, ToolSecurityPolicy


class FakeSecurityPolicy:
    def authorize(self, tool_name: str) -> ToolDecision:
        return ToolDecision(tool_name == "echo", "fake decision")


class ToolSecurityPolicyTests(unittest.TestCase):
    def test_allowlisted_tool_is_authorized(self):
        decision = ToolSecurityPolicy().authorize("echo")
        self.assertTrue(decision.allowed)
    def test_unlisted_tool_is_rejected(self):
        decision = ToolSecurityPolicy().authorize("shell")
        self.assertFalse(decision.allowed); self.assertEqual(decision.reason, "tool is not allowlisted")
    def test_empty_tool_name_is_rejected(self):
        decision = ToolSecurityPolicy().authorize("   ")
        self.assertFalse(decision.allowed)
    def test_fake_policy_satisfies_security_contract(self):
        policy: SecurityPolicy = FakeSecurityPolicy()
        self.assertTrue(policy.authorize("echo").allowed)
        self.assertFalse(policy.authorize("shell").allowed)

if __name__ == "__main__": unittest.main()
