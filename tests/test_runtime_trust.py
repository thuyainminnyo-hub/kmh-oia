import unittest
from src.runtime_trust import RuntimeTrustEngine
from src.real_execution_verification import VerificationResult


class RuntimeTrustTests(unittest.TestCase):
    def test_failed_verification_is_unproven(self):
        v = VerificationResult("exec-1", False, {"identity": False}, "failed")
        d = RuntimeTrustEngine().decide(v, governance_approved=True)
        self.assertEqual(d.level, "UNPROVEN")
        self.assertFalse(d.trusted)

    def test_verified_without_governance_is_conditional(self):
        v = VerificationResult("exec-1", True, {"identity": True}, "verified")
        d = RuntimeTrustEngine().decide(v)
        self.assertEqual(d.level, "CONDITIONAL")
        self.assertFalse(d.trusted)

    def test_verified_and_governed_is_proven(self):
        v = VerificationResult("exec-1", True, {"identity": True}, "verified")
        d = RuntimeTrustEngine().decide(v, governance_approved=True)
        self.assertEqual(d.level, "PROVEN")
        self.assertTrue(d.trusted)


if __name__ == "__main__":
    unittest.main()
