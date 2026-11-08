from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from src.trailrun_incident_service import (
    AccessDenied,
    InvalidIncidentPayload,
    TrailRunIncidentService,
)
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
        self.service = TrailRunIncidentService(
            store, allowed_checkpoint_ids={"cp_DEMO_SVC"}
        )
        self.service.create_incident("checkpoint_volunteer", payload())

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_incident_outside_checkpoint_scope_is_denied_without_create_side_effects(self):
        outside = payload()
        outside["incident_id"] = "inc_OUTSIDE_SCOPE"
        outside["event_id"] = "evt_OUTSIDE_SCOPE"
        outside["checkpoint_id"] = "cp_OTHER"
        with self.assertRaises(AccessDenied):
            self.service.create_incident("checkpoint_volunteer", outside)

        # A denied create must leave no incident, receipt, or audit entry behind.
        self.assertIsNone(self.service._store.get_incident("inc_OUTSIDE_SCOPE"))
        self.assertEqual(self.service._store.get_audit("inc_OUTSIDE_SCOPE"), [])
        seed_result = self.service._store.create_incident(outside)
        self.assertTrue(
            seed_result.created,
            "scope-denied creation must not leave an idempotency receipt",
        )

        # Seed through the low-level store to simulate an existing incident
        # owned by another checkpoint; the service must still deny access.
        with self.assertRaises(AccessDenied):
            self.service.get_incident("race_control", "inc_OUTSIDE_SCOPE")
        with self.assertRaises(AccessDenied):
            self.service.get_audit("race_control", "inc_OUTSIDE_SCOPE")

        with self.assertRaises(AccessDenied):
            self.service.transition(
                "race_control", "inc_OUTSIDE_SCOPE", "ACKNOWLEDGED",
                at="2026-10-28T02:03:00Z",
            )
        outside_after = self.service._store.get_incident("inc_OUTSIDE_SCOPE")
        self.assertEqual(outside_after["status"], "REPORTED")
        self.assertEqual(
            len(self.service._store.get_audit("inc_OUTSIDE_SCOPE")), 1
        )

    def test_missing_checkpoint_scope_denies_create_without_side_effects(self):
        deny_by_default = TrailRunIncidentService(self.service._store)
        candidate = payload()
        candidate["incident_id"] = "inc_NO_SCOPE"
        candidate["event_id"] = "evt_NO_SCOPE"

        with self.assertRaises(AccessDenied):
            deny_by_default.create_incident("checkpoint_volunteer", candidate)

        self.assertIsNone(self.service._store.get_incident("inc_NO_SCOPE"))
        self.assertEqual(self.service._store.get_audit("inc_NO_SCOPE"), [])
        seed_result = self.service._store.create_incident(candidate)
        self.assertTrue(
            seed_result.created,
            "default-denied creation must not leave an idempotency receipt",
        )

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

    def test_create_rejects_audit_actor_role_mismatch_without_side_effects(self):
        bad = payload()
        bad["incident_id"] = "inc_AUDIT_ROLE_MISMATCH"
        bad["event_id"] = "evt_AUDIT_ROLE_MISMATCH"
        bad["audit"][0]["actor_role"] = "medical_lead"

        with self.assertRaises(AccessDenied):
            self.service.create_incident("checkpoint_volunteer", bad)

        self.assertIsNone(
            self.service._store.get_incident("inc_AUDIT_ROLE_MISMATCH")
        )
        self.assertEqual(
            self.service._store.get_audit("inc_AUDIT_ROLE_MISMATCH"), []
        )
        seed_result = self.service._store.create_incident(bad)
        self.assertTrue(
            seed_result.created,
            "audit-attribution rejection must not leave an idempotency receipt",
        )

    def test_create_rejects_location_only_payload_without_checkpoint_scope(self):
        bad = payload()
        bad["incident_id"] = "inc_NO_CHECKPOINT_SCOPE"
        bad["event_id"] = "evt_NO_CHECKPOINT_SCOPE"
        bad.pop("checkpoint_id")
        bad["last_known_location"] = {
            "description": "Synthetic location only; test fixture.",
            "observed_at": "2026-10-28T02:00:00Z",
        }

        with self.assertRaises(InvalidIncidentPayload):
            self.service.create_incident("checkpoint_volunteer", bad)

        self.assertIsNone(
            self.service._store.get_incident("inc_NO_CHECKPOINT_SCOPE")
        )
        self.assertEqual(
            self.service._store.get_audit("inc_NO_CHECKPOINT_SCOPE"), []
        )

    def test_create_rejects_prepopulated_audit_history_without_side_effects(self):
        bad = payload()
        bad["incident_id"] = "inc_PREPOPULATED_AUDIT"
        bad["event_id"] = "evt_PREPOPULATED_AUDIT"
        bad["audit"].append({
            "action": "ACKNOWLEDGED",
            "actor_role": "race_control",
            "at": "2026-10-28T02:01:00Z",
            "result": "completed",
            "correlation_id": "corr_PREPOPULATED_AUDIT",
        })

        with self.assertRaises(InvalidIncidentPayload):
            self.service.create_incident("checkpoint_volunteer", bad)

        self.assertIsNone(self.service._store.get_incident("inc_PREPOPULATED_AUDIT"))
        self.assertEqual(self.service._store.get_audit("inc_PREPOPULATED_AUDIT"), [])

    def test_create_rejects_non_reported_initial_audit_action(self):
        bad = payload()
        bad["incident_id"] = "inc_BAD_INITIAL_AUDIT_ACTION"
        bad["event_id"] = "evt_BAD_INITIAL_AUDIT_ACTION"
        bad["audit"][0]["action"] = "ACKNOWLEDGED"

        with self.assertRaises(InvalidIncidentPayload):
            self.service.create_incident("checkpoint_volunteer", bad)

        self.assertIsNone(
            self.service._store.get_incident("inc_BAD_INITIAL_AUDIT_ACTION")
        )
        self.assertEqual(
            self.service._store.get_audit("inc_BAD_INITIAL_AUDIT_ACTION"), []
        )

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

    def test_transitioned_payload_remains_schema_valid_and_matches_audit_log(self):
        self.service.transition(
            "race_control", "inc_SYNTHETIC_SVC", "ACKNOWLEDGED",
            at="2026-10-28T02:01:00Z",
            correlation_id="corr_ACK_SCHEMA",
        )
        incident = self.service.get_incident("race_control", "inc_SYNTHETIC_SVC")
        audit_rows = self.service.get_audit("race_control", "inc_SYNTHETIC_SVC")

        self.assertEqual(incident["status"], incident["payload"]["status"])
        self.assertEqual(len(incident["payload"]["audit"]), len(audit_rows))

        payload_audit = [
            {
                "action": entry["action"],
                "actor_role": entry["actor_role"],
                "at": entry["at"],
                "result": entry["result"],
                "correlation_id": entry.get("correlation_id"),
            }
            for entry in incident["payload"]["audit"]
        ]
        database_audit = [
            {
                "action": entry["action"],
                "actor_role": entry["actor_role"],
                "at": entry["at"],
                "result": entry["result"],
                "correlation_id": entry["correlation_id"],
            }
            for entry in audit_rows
        ]
        self.assertEqual(payload_audit, database_audit)

        schema_path = (
            Path(__file__).resolve().parents[1]
            / "docs" / "pilots" / "tgi-trailrun-2026" / "incident.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = Draft202012Validator(
            schema, format_checker=Draft202012Validator.FORMAT_CHECKER
        )
        self.assertEqual(list(validator.iter_errors(incident["payload"])), [])

    def test_medical_lead_can_resolve_but_cannot_dispatch(self):
        with self.assertRaises(AccessDenied):
            self.service.transition(
                "medical_lead", "inc_SYNTHETIC_SVC", "DISPATCHED",
                at="2026-10-28T02:01:00Z",
            )

    def test_volunteer_cannot_read_audit(self):
        with self.assertRaises(AccessDenied):
            self.service.get_audit("checkpoint_volunteer", "inc_SYNTHETIC_SVC")

    def test_service_rejects_schema_invalid_payload_before_persistence(self):
        bad = payload()
        bad["incident_id"] = "inc_SCHEMA_BAD"
        bad["event_id"] = "evt_SCHEMA_BAD"
        bad["unexpected_field"] = "must be rejected"
        with self.assertRaises(InvalidIncidentPayload):
            self.service.create_incident("checkpoint_volunteer", bad)
        self.assertIsNone(
            self.service.get_incident("race_control", "inc_SCHEMA_BAD")
        )

    def test_create_role_must_match_reporter_role_without_side_effects(self):
        bad = payload()
        bad["incident_id"] = "inc_MISMATCH"
        bad["event_id"] = "evt_MISMATCH"
        with self.assertRaises(AccessDenied):
            self.service.create_incident("race_control", bad)

        self.assertIsNone(self.service._store.get_incident("inc_MISMATCH"))
        self.assertEqual(self.service._store.get_audit("inc_MISMATCH"), [])
        seed_result = self.service._store.create_incident(bad)
        self.assertTrue(
            seed_result.created,
            "role-mismatch rejection must not leave an idempotency receipt",
        )


if __name__ == "__main__":
    unittest.main()
