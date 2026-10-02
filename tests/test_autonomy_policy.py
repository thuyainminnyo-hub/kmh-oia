import unittest

from src.autonomy_policy import AutonomyPolicy


class AutonomyPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = AutonomyPolicy({"read", "summarize"}, {"local", "staging"})

    def test_declared_action_and_scope_are_allowed(self):
        self.assertTrue(self.policy.evaluate("read", "local").allowed)

    def test_undeclared_action_is_denied(self):
        decision = self.policy.evaluate("delete", "local")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "action is not allowlisted")

    def test_undeclared_scope_is_denied(self):
        decision = self.policy.evaluate("read", "production")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "scope is not allowlisted")

    def test_matching_is_exact(self):
        self.assertFalse(self.policy.evaluate("READ", "local").allowed)
        self.assertFalse(self.policy.evaluate("read", "Local").allowed)

    def test_empty_inputs_are_denied(self):
        self.assertFalse(self.policy.evaluate(" ", "local").allowed)
        self.assertFalse(self.policy.evaluate("read", "").allowed)


if __name__ == "__main__":
    unittest.main()
