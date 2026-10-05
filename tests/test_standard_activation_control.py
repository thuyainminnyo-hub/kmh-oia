import unittest

from src.standard_activation_control import StandardActivationControl
from src.standardization_engine import OperatingStandard


class StandardActivationControlTests(unittest.TestCase):
    def test_proposed_standard_requires_explicit_approval_before_activation(self):
        standard = OperatingStandard("std:a:v2", "a", "Require evidence and QA", "Better quality", 2, "PROPOSED")
        control = StandardActivationControl()
        with self.assertRaises(ValueError):
            control.activate(standard)

    def test_approve_then_activate_registers_active_version(self):
        standard = OperatingStandard("std:a:v2", "a", "Require evidence and QA", "Better quality", 2, "PROPOSED")
        control = StandardActivationControl()
        approved = control.approve(standard)
        self.assertEqual(approved.standard.status, "APPROVED")
        activated = control.activate(approved.standard)
        self.assertTrue(activated.activated)
        self.assertEqual(activated.standard.status, "ACTIVE")
        self.assertEqual(control.active("a").id, "std:a:v2")

    def test_activation_rejects_second_active_version(self):
        control = StandardActivationControl()
        first = OperatingStandard("std:a:v1", "a", "Require evidence", "Quality", 1, "ACTIVE")
        second = OperatingStandard("std:a:v2", "a", "Require evidence and QA", "Better quality", 2, "APPROVED")
        control.registry.register(first)
        with self.assertRaises(ValueError):
            control.activate(second)

    def test_approve_and_activate_is_still_explicitly_governed(self):
        standard = OperatingStandard("std:b:v1", "b", "Require evidence", "Quality", 1, "PROPOSED")
        result = StandardActivationControl().approve_and_activate(standard)
        self.assertTrue(result.approved)
        self.assertTrue(result.activated)
        self.assertEqual(result.standard.status, "ACTIVE")


if __name__ == "__main__":
    unittest.main()
