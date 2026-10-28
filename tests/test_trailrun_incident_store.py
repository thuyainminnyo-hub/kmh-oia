from __future__ import annotations

import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from src.trailrun_incident_store import (
    IdempotencyConflict,
    IncidentIdConflict,
    InvalidIncident,
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

    def test_reused_incident_id_with_new_event_is_conflict_without_side_effects(self):
        first = self.store.create_incident(
            sample_incident(
                event_id="evt_ORIGINAL001",
                incident_id="inc_DUPLICATE001",
            )
        )
        conflicting = sample_incident(
            event_id="evt_SECONDARY001",
            incident_id="inc_DUPLICATE001",
        )

        with self.assertRaises(IncidentIdConflict):
            self.store.create_incident(conflicting)

        saved = self.store.get_incident("inc_DUPLICATE001")
        self.assertEqual(saved["payload"]["event_id"], "evt_ORIGINAL001")
        self.assertEqual(len(self.store.get_audit("inc_DUPLICATE001")), 1)

        # The failed create must not leave an idempotency receipt for its event.
        retry = dict(conflicting)
        retry["incident_id"] = "inc_FRESH002"
        retry_result = self.store.create_incident(retry)
        self.assertTrue(retry_result.created)
        self.assertEqual(retry_result.incident_id, "inc_FRESH002")
        self.assertEqual(len(self.store.get_audit("inc_DUPLICATE001")), 1)
        self.assertTrue(first.created)

    def test_transition_and_audit_are_both_persisted(self):
        self.store.create_incident(sample_incident())
        result = self.store.transition(
            "inc_SYNTHETIC001", "ACKNOWLEDGED",
            actor_role="medical_lead", at="2026-10-28T02:01:00Z",
            correlation_id="corr_ACK001",
        )
        self.assertEqual(result["status"], "ACKNOWLEDGED")
        saved = self.store.get_incident("inc_SYNTHETIC001")
        audit_rows = self.store.get_audit("inc_SYNTHETIC001")
        self.assertEqual(saved["status"], "ACKNOWLEDGED")
        self.assertEqual(saved["payload"]["status"], "ACKNOWLEDGED")
        self.assertEqual(len(audit_rows), 2)
        self.assertEqual(len(saved["payload"]["audit"]), 2)

        payload_audit = [
            {
                "action": item["action"],
                "actor_role": item["actor_role"],
                "at": item["at"],
                "result": item["result"],
                "correlation_id": item.get("correlation_id"),
            }
            for item in saved["payload"]["audit"]
        ]
        database_audit = [
            {
                "action": item["action"],
                "actor_role": item["actor_role"],
                "at": item["at"],
                "result": item["result"],
                "correlation_id": item["correlation_id"],
            }
            for item in audit_rows
        ]
        self.assertEqual(payload_audit, database_audit)

    def test_transition_fails_closed_when_embedded_audit_differs_from_authoritative_log(self):
        self.store.create_incident(sample_incident())
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT payload_json FROM incidents WHERE incident_id=?",
                ("inc_SYNTHETIC001",),
            ).fetchone()
            tampered = json.loads(row[0])
            tampered["audit"][0]["result"] = "forged"
            connection.execute(
                "UPDATE incidents SET payload_json=? WHERE incident_id=?",
                (json.dumps(tampered), "inc_SYNTHETIC001"),
            )

        audit_before = self.store.get_audit("inc_SYNTHETIC001")

        # Both read and transition boundaries must fail closed on divergent history.
        with self.assertRaises(InvalidIncident):
            self.store.get_incident("inc_SYNTHETIC001")
        with self.assertRaises(InvalidIncident):
            self.store.transition(
                "inc_SYNTHETIC001", "ACKNOWLEDGED",
                actor_role="race_control", at="2026-10-28T02:01:00Z",
            )

        with sqlite3.connect(self.db_path) as connection:
            row_after = connection.execute(
                "SELECT status, payload_json FROM incidents WHERE incident_id=?",
                ("inc_SYNTHETIC001",),
            ).fetchone()
        saved_payload = json.loads(row_after[1])
        self.assertEqual(row_after[0], "REPORTED")
        self.assertEqual(saved_payload["status"], "REPORTED")
        self.assertEqual(saved_payload["audit"][0]["result"], "forged")
        self.assertEqual(self.store.get_audit("inc_SYNTHETIC001"), audit_before)

    def test_direct_store_call_cannot_bypass_transition_role_policy(self):
        self.store.create_incident(sample_incident())
        self.store.transition(
            "inc_SYNTHETIC001", "ACKNOWLEDGED",
            actor_role="race_control", at="2026-10-28T02:01:00Z",
        )
        before_audit = len(self.store.get_audit("inc_SYNTHETIC001"))
        with self.assertRaises(InvalidTransition):
            self.store.transition(
                "inc_SYNTHETIC001", "DISPATCHED",
                actor_role="checkpoint_volunteer", at="2026-10-28T02:02:00Z",
            )
        self.assertEqual(
            self.store.get_incident("inc_SYNTHETIC001")["status"], "ACKNOWLEDGED"
        )
        self.assertEqual(len(self.store.get_audit("inc_SYNTHETIC001")), before_audit)

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

    def test_concurrent_competing_transitions_apply_once_and_audit_once(self):
        self.store.create_incident(sample_incident())
        barrier = threading.Barrier(2)
        results = []
        errors = []

        def submit(correlation_id: str) -> None:
            try:
                barrier.wait(timeout=3)
                result = SQLiteIncidentStore(self.db_path).transition(
                    "inc_SYNTHETIC001", "ACKNOWLEDGED",
                    actor_role="race_control",
                    at="2026-10-28T02:01:00Z",
                    correlation_id=correlation_id,
                )
                results.append(result)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=submit, args=("corr_RACE_A",)),
            threading.Thread(target=submit, args=("corr_RACE_B",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(len(results), 1, repr(results))
        self.assertEqual(len(errors), 1, repr(errors))
        self.assertIsInstance(errors[0], InvalidTransition)

        saved = self.store.get_incident("inc_SYNTHETIC001")
        audit_rows = self.store.get_audit("inc_SYNTHETIC001")
        self.assertEqual(saved["status"], "ACKNOWLEDGED")
        self.assertEqual(saved["payload"]["status"], "ACKNOWLEDGED")
        self.assertEqual(len(audit_rows), 2)
        self.assertEqual(len(saved["payload"]["audit"]), 2)
        self.assertEqual(
            saved["payload"]["audit"][-1]["correlation_id"],
            audit_rows[-1]["correlation_id"],
        )

    def test_create_rejects_multiple_initial_audit_entries_at_store_boundary(self):
        invalid = sample_incident(
            event_id="evt_MULTI_AUDIT",
            incident_id="inc_MULTI_AUDIT",
        )
        invalid["audit"].append({
            "action": "ACKNOWLEDGED",
            "actor_role": "race_control",
            "at": "2026-10-28T02:01:00Z",
            "result": "completed",
            "correlation_id": "corr_MULTI_AUDIT",
        })

        with self.assertRaises(InvalidIncident):
            self.store.create_incident(invalid)

        self.assertIsNone(self.store.get_incident("inc_MULTI_AUDIT"))
        self.assertEqual(self.store.get_audit("inc_MULTI_AUDIT"), [])

    def test_invalid_new_status_is_rejected(self):
        invalid = sample_incident()
        invalid["status"] = "DISPATCHED"
        with self.assertRaises(InvalidIncident):
            self.store.create_incident(invalid)


if __name__ == "__main__":
    unittest.main()
