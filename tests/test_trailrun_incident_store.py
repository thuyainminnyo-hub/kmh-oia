from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path

from src.trailrun_incident_store import (
    IdempotencyConflict,
    InvalidTransition,
    SQLiteIncidentStore,
)


def sample_incident(event_id: str = "evt_SYNTHETIC001", incident_id: str = "inc_SYNTHETIC001"):
    return {
        "schema_version": "1.0",
        "incident_id": incident_id,
        "event_id": event_id,
        "event_type": "runner_assistance_requested",
        "severity": "P2",
        "status": "REPORTED",
        "occurred_at": "2026-10-28T02:00:00Z",
        "recorded_at": "2026-10-28T02:00:05Z",
        "runner_id": "run_DEMO001",
        "checkpoint_id": "cp_DEMO01",
        "reported_by_role": "checkpoint_volunteer",
        "summary_code": "NEEDS_CHECK",
        "operator_note": "Synthetic test only.",
        "audit": [{
            "action": "REPORTED",
            "actor_role": "checkpoint_volunteer",
            "at": "2026-10-28T02:00:05Z",
            "result": "accepted",
            "correlation_id": "corr_SYNTHETIC001"
        }]
    }


class TrailRunIncidentStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "pilot.sqlite3"
        self.store = SQLiteIncidentStore(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_read_incident(self):
        result = self.store.create_incident(sample_incident())
        self.assertTrue(result.created)
        saved = self.store.get_incident(result.incident_id)
        self.assertEqual(saved["status"], "REPORTED")
        self.assertEqual(saved["payload"]["event_id"], result.event_id)

    def test_exact_duplicate_event_is_idempotent(self):
        first = self.store.create_incident(sample_incident())
        second = self.store.create_incident(sample_incident())
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.incident_id, second.incident_id)
        self.assertEqual(len(self.store.get_audit(first.incident_id)), 1)

    def test_reused_event_id_with_changed_payload_is_conflict(self):
        self.store.create_incident(sample_incident())
        changed = sample_incident()
        changed["severity"] = "P1"
        with self.assertRaises(IdempotencyConflict):
            self.store.create_incident(changed)

    def test_transition_and_audit_are_both_persisted(self):
        self.store.create_incident(sample_incident())
        result = self.store.transition(
            "inc_SYNTHETIC001", "ACKNOWLEDGED",
            actor_role="medical_lead", at="2026-10-28T02:01:00Z",
            correlation_id="corr_ACK001",
        )
        self.assertEqual(result["status"], "ACKNOWLEDGED")
        self.assertEqual(self.store.get_incident("inc_SYNTHETIC001")["status"], "ACKNOWLEDGED")
        self.assertEqual(len(self.store.get_audit("inc_SYNTHETIC001")), 2)

    def test_invalid_transition_does_not_change_status_or_audit(self):
        self.store.create_incident(sample_incident())
        with self.assertRaises(InvalidTransition):
            self.store.transition(
                "inc_SYNTHETIC001", "DISPATCHED",
                actor_role="race_control", at="2026-10-28T02:01:00Z",
            )
        self.assertEqual(self.store.get_incident("inc_SYNTHETIC001")["status"], "REPORTED")
        self.assertEqual(len(self.store.get_audit("inc_SYNTHETIC001")), 1)

    def test_file_database_survives_store_recreation(self):
        self.store.create_incident(sample_incident())
        restarted_store = SQLiteIncidentStore(self.db_path)
        self.assertEqual(
            restarted_store.get_incident("inc_SYNTHETIC001")["status"], "REPORTED"
        )
        self.assertEqual(len(restarted_store.get_audit("inc_SYNTHETIC001")), 1)

    def test_concurrent_duplicate_submission_creates_one_incident(self):
        results = []
        errors = []
        barrier = threading.Barrier(2)

        def submit():
            try:
                barrier.wait(timeout=3)
                results.append(SQLiteIncidentStore(self.db_path).create_incident(sample_incident()))
            except Exception as exc:  # surfaced to assertion below
                errors.append(exc)

        threads = [threading.Thread(target=submit) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertFalse(errors, repr(errors))
        self.assertEqual(len(results), 2)
        self.assertEqual(sum(result.created for result in results), 1)
        self.assertEqual(len(self.store.get_audit("inc_SYNTHETIC001")), 1)

    def test_invalid_new_status_is_rejected(self):
        invalid = sample_incident()
        invalid["status"] = "DISPATCHED"
        with self.assertRaises(ValueError):
            self.store.create_incident(invalid)


if __name__ == "__main__":
    unittest.main()
