import unittest

from src.security import ToolSecurityPolicy


class ToolSecurityPolicyTests(unittest.TestCase):
    def test_allowlisted_tool_is_authorized(self):
        decision = ToolSecurityPolicy().authorize("echo")
        self.assertTrue(decision.allowed)

    def test_unlisted_tool_is_rejected(self):
        decision = ToolSecurityPolicy().authorize("shell")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "tool is not allowlisted")

    def test_empty_tool_name_is_rejected(self):
        decision = ToolSecurityPolicy().authorize("   ")
        self.assertFalse(decision.allowed)


if __name__ == "__main__":
    unittest.main()
