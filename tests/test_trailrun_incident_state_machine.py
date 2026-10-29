import unittest

from src.trailrun_incident_state_machine import (
    ALLOWED_TRANSITIONS,
    validate_transition,
)


class TrailRunIncidentStateMachineTests(unittest.TestCase):
    def test_all_documented_transitions_are_allowed(self):
        for current, requested in ALLOWED_TRANSITIONS:
            with self.subTest(current=current, requested=requested):
                decision = validate_transition(current, requested)
                self.assertTrue(decision.allowed)
                self.assertEqual(decision.reason_code, "TRANSITION_ALLOWED")

    def test_skipping_acknowledgement_is_rejected(self):
        decision = validate_transition("REPORTED", "DISPATCHED")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, "INVALID_TRANSITION")

    def test_cannot_close_before_resolution(self):
        decision = validate_transition("DISPATCHED", "CLOSED")
        self.assertFalse(decision.allowed)

    def test_unknown_status_is_rejected(self):
        decision = validate_transition("UNKNOWN", "CLOSED")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, "UNKNOWN_STATUS")

    def test_same_state_is_rejected_as_noop(self):
        decision = validate_transition("REPORTED", "REPORTED")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, "NO_OP_NOT_ALLOWED")

    def test_decision_is_side_effect_free(self):
        current = "REPORTED"
        decision = validate_transition(current, "ACKNOWLEDGED")
        self.assertTrue(decision.allowed)
        self.assertEqual(current, "REPORTED")


if __name__ == "__main__":
    unittest.main()
