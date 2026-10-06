import unittest
from src.standardization_engine import OperatingStandard
from src.standardization_governance_bridge import StandardizationGovernanceBridge

class StandardizationGovernanceBridgeTests(unittest.TestCase):
    def test_approved_review_stops_at_approved_until_activation(self):
        bridge = StandardizationGovernanceBridge()
        standard = OperatingStandard("std:a:v1", "a", "Require evidence", "Quality", 1, "PROPOSED")
        review = bridge.review(standard, approved=True, reason="Improved experiment is evidence-backed")
        self.assertEqual(review.decision, "APPROVED")
        self.assertEqual(review.activation.standard.status, "APPROVED")
        self.assertIsNone(bridge.control.active("a"))

    def test_activation_requires_approved_review(self):
        bridge = StandardizationGovernanceBridge()
        standard = OperatingStandard("std:a:v1", "a", "Require evidence", "Quality", 1, "PROPOSED")
        review = bridge.review(standard, approved=False, reason="Insufficient evidence")
        with self.assertRaises(ValueError):
            bridge.activate(review)

    def test_approved_review_can_activate_explicitly(self):
        bridge = StandardizationGovernanceBridge()
        standard = OperatingStandard("std:b:v1", "b", "Require evidence", "Quality", 1, "PROPOSED")
        review = bridge.review(standard, approved=True, reason="Validated improvement")
        result = bridge.activate(review)
        self.assertTrue(result.activated)
        self.assertEqual(result.standard.status, "ACTIVE")

if __name__ == "__main__":
    unittest.main()
