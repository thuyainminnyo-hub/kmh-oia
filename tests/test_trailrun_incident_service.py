from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.trailrun_incident_service import AccessDenied, TrailRunIncidentService
from src.trailrun_incident_store import SQLiteIncidentStore


def payload():
    return {
        "schema_version": "1.0",
        "incident_id": "inc_SYNTHETIC_SVC",
        "event_id": "evt_SYNTHETIC_SVC",
        "event_type": "runner_assistance_requested",
        "severity": "P2",
        "status": "REPORTED",
        "occurred_at": "2026-10-28T02:00:00Z",
        "recorded_at": "2026-10-28T02:00:05Z",
        "runner_id": "run_DEMO_SVC",
        "checkpoint_id": "cp_DEMO_SVC",
        "reported_by_role": "checkpoint_volunteer",
        "summary_code": "NEEDS_CHECK",
        "operator_note": "Synthetic test only.",
        "audit": [{
            "action": "REPORTED",
            "actor_role": "checkpoint_volunteer",
            "at": "2026-10-28T02:00:05Z",
            "result": "accepted",
            "correlation_id": "corr_SYNTHETIC_SVC",
        }],
    }


class TrailRunIncidentServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        store = SQLiteIncidentStore(Path(self.temp_dir.name) / "service.sqlite3")
        self.service = TrailRunIncidentService(store)
        self.service.create_incident("checkpoint_volunteer", payload())

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_volunteer_cannot_dispatch_and_state_audit_unchanged(self):
        with self.assertRaises(AccessDenied):
            self.service.transition(
                "checkpoint_volunteer", "inc_SYNTHETIC_SVC", "DISPATCHED",
                at="2026-10-28T02:01:00Z",
            )
        self.assertEqual(
            self.service.get_incident("race_control", "inc_SYNTHETIC_SVC")["status"],
            "REPORTED",
        )
        self.assertEqual(len(self.service.get_audit("race_control", "inc_SYNTHETIC_SVC")), 1)

    def test_race_control_can_acknowledge_then_dispatch(self):
        self.service.transition(
            "race_control", "inc_SYNTHETIC_SVC", "ACKNOWLEDGED",
            at="2026-10-28T02:01:00Z",
        )
        self.service.transition(
            "race_control", "inc_SYNTHETIC_SVC", "DISPATCHED",
            at="2026-10-28T02:02:00Z",
        )
        self.assertEqual(
            self.service.get_incident("race_control", "inc_SYNTHETIC_SVC")["status"],
            "DISPATCHED",
        )

    def test_medical_lead_can_resolve_but_cannot_dispatch(self):
        with self.assertRaises(AccessDenied):
            self.service.transition(
                "medical_lead", "inc_SYNTHETIC_SVC", "DISPATCHED",
                at="2026-10-28T02:01:00Z",
            )

    def test_volunteer_cannot_read_audit(self):
        with self.assertRaises(AccessDenied):
            self.service.get_audit("checkpoint_volunteer", "inc_SYNTHETIC_SVC")

    def test_create_role_must_match_reporter_role(self):
        bad = payload()
        bad["incident_id"] = "inc_MISMATCH"
        bad["event_id"] = "evt_MISMATCH"
        with self.assertRaises(AccessDenied):
            self.service.create_incident("race_control", bad)


if __name__ == "__main__":
    unittest.main()
