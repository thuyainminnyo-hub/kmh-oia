import unittest

from src.security import ToolSecurityPolicy


class Stage13SecurityBoundaryTests(unittest.TestCase):
    def test_default_policy_allows_only_echo(self):
        policy = ToolSecurityPolicy()
        self.assertTrue(policy.authorize("echo").allowed)
        self.assertFalse(policy.authorize("shell").allowed)
        self.assertFalse(policy.authorize("http").allowed)

    def test_explicit_allowlist_isolated_from_default(self):
        policy = ToolSecurityPolicy({"safe_tool"})
        self.assertTrue(policy.authorize("safe_tool").allowed)
        self.assertFalse(policy.authorize("echo").allowed)

    def test_blank_and_whitespace_tool_names_are_denied(self):
        policy = ToolSecurityPolicy({"echo"})
        for tool_name in ("", " ", "\t", "\n"):
            decision = policy.authorize(tool_name)
            self.assertFalse(decision.allowed)
            self.assertIn("must not be empty", decision.reason)

    def test_near_match_names_are_not_authorized(self):
        policy = ToolSecurityPolicy({"echo"})
        for tool_name in ("Echo", " echo", "echo ", "echo\n"):
            self.assertFalse(policy.authorize(tool_name).allowed)

    def test_allowlist_input_is_not_mutated(self):
        allowed = {"echo"}
        policy = ToolSecurityPolicy(allowed)
        allowed.add("shell")
        self.assertFalse(policy.authorize("shell").allowed)


if __name__ == "__main__":
    unittest.main()
