from __future__ import annotations

import unittest

from src.trailrun_incident_access import authorize, authorize_transition


class TrailRunIncidentAccessTests(unittest.TestCase):
    def test_unknown_role_denied_by_default(self):
        result = authorize("unknown_role", "incident:read")
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason_code, "UNKNOWN_ROLE")

    def test_checkpoint_volunteer_can_create_but_not_dispatch(self):
        self.assertTrue(authorize("checkpoint_volunteer", "incident:create").allowed)
        self.assertFalse(authorize_transition("checkpoint_volunteer", "DISPATCHED").allowed)

    def test_race_control_can_dispatch_but_not_resolve_medical_incident(self):
        self.assertTrue(authorize_transition("race_control", "DISPATCHED").allowed)
        self.assertFalse(authorize_transition("race_control", "RESOLVED").allowed)

    def test_medical_lead_can_resolve_but_not_dispatch(self):
        self.assertTrue(authorize_transition("medical_lead", "RESOLVED").allowed)
        self.assertFalse(authorize_transition("medical_lead", "DISPATCHED").allowed)

    def test_audit_is_restricted_to_control_and_medical_lead(self):
        self.assertTrue(authorize("race_control", "audit:read").allowed)
        self.assertTrue(authorize("medical_lead", "audit:read").allowed)
        self.assertFalse(authorize("checkpoint_volunteer", "audit:read").allowed)

    def test_unknown_action_denied(self):
        self.assertFalse(authorize("race_control", "incident:delete").allowed)

    def test_policy_does_not_authenticate_identity(self):
        # Policy checks only supplied role/action; caller must authenticate identity.
        self.assertTrue(authorize("race_control", "incident:read").allowed)


if __name__ == "__main__":
    unittest.main()
