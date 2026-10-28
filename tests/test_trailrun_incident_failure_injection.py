"""Synthetic failure-injection tests for SQLite transaction atomicity.

These tests use a temporary local database and synthetic IDs only. They do not
exercise live identity, notification, dispatch, or production infrastructure.
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.trailrun_incident_store import SQLiteIncidentStore


def synthetic_incident(
    event_id: str = "evt_FAILURE_INJECT_01",
    incident_id: str = "inc_FAILURE_INJECT_01",
) -> dict:
    return {
        "schema_version": "1.0",
        "incident_id": incident_id,
        "event_id": event_id,
        "event_type": "runner_assistance_requested",
        "severity": "P2",
        "status": "REPORTED",
        "occurred_at": "2026-10-28T02:00:00Z",
        "recorded_at": "2026-10-28T02:00:05Z",
        "runner_id": "run_DEMO_FAILURE",
        "checkpoint_id": "cp_DEMO_FAILURE",
        "reported_by_role": "checkpoint_volunteer",
        "summary_code": "NEEDS_CHECK",
        "operator_note": "Synthetic failure-injection fixture only.",
        "audit": [
            {
                "action": "REPORTED",
                "actor_role": "checkpoint_volunteer",
                "at": "2026-10-28T02:00:05Z",
                "result": "accepted",
                "correlation_id": "corr_FAILURE_INJECT_01",
            }
        ],
    }


class TrailRunFailureInjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "failure-injection.sqlite3"
        self.store = SQLiteIncidentStore(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def table_counts(self, incident_id: str, event_id: str) -> tuple[int, int, int]:
        with sqlite3.connect(self.database_path) as connection:
            incident_count = connection.execute(
                "SELECT COUNT(*) FROM incidents WHERE incident_id=?",
                (incident_id,),
            ).fetchone()[0]
            receipt_count = connection.execute(
                "SELECT COUNT(*) FROM event_receipts WHERE event_id=?",
                (event_id,),
            ).fetchone()[0]
            audit_count = connection.execute(
                "SELECT COUNT(*) FROM incident_audit WHERE incident_id=?",
                (incident_id,),
            ).fetchone()[0]
        return incident_count, receipt_count, audit_count

    def test_failed_receipt_insert_rolls_back_create_and_allows_clean_retry(self) -> None:
        incident = synthetic_incident()

        # Inject a deterministic failure after the incident row would be inserted
        # but before the event receipt and audit entry can complete.
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TRIGGER inject_receipt_failure
                BEFORE INSERT ON event_receipts
                BEGIN
                    SELECT RAISE(ABORT, 'synthetic receipt write failure');
                END;
                """
            )

        with self.assertRaisesRegex(sqlite3.IntegrityError, "synthetic receipt write failure"):
            self.store.create_incident(incident)

        # The failed transaction must leave no partial incident, receipt, or audit.
        self.assertEqual(
            self.table_counts(incident["incident_id"], incident["event_id"]),
            (0, 0, 0),
        )
        self.assertIsNone(self.store.get_incident(incident["incident_id"]))
        self.assertEqual(self.store.get_audit(incident["incident_id"]), [])

        # Remove only the test fault and verify a fresh request can succeed.
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("DROP TRIGGER inject_receipt_failure")

        created = self.store.create_incident(incident)
        replay = self.store.create_incident(incident)
        self.assertTrue(created.created)
        self.assertFalse(replay.created)
        self.assertEqual(
            self.table_counts(incident["incident_id"], incident["event_id"]),
            (1, 1, 1),
        )

    def test_failed_transition_audit_insert_rolls_back_state_change(self) -> None:
        incident = synthetic_incident(
            event_id="evt_FAILURE_TRANSITION_01",
            incident_id="inc_FAILURE_TRANSITION_01",
        )
        self.store.create_incident(incident)

        # The state update occurs before the audit insert; failure at the latter
        # must roll back both operations in the same transaction.
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TRIGGER inject_transition_audit_failure
                BEFORE INSERT ON incident_audit
                WHEN NEW.action = 'ACKNOWLEDGED'
                BEGIN
                    SELECT RAISE(ABORT, 'synthetic audit write failure');
                END;
                """
            )

        with self.assertRaisesRegex(sqlite3.IntegrityError, "synthetic audit write failure"):
            self.store.transition(
                incident["incident_id"],
                "ACKNOWLEDGED",
                actor_role="race_control",
                at="2026-10-28T02:01:00Z",
                correlation_id="corr_FAILURE_TRANSITION_01",
            )

        saved = self.store.get_incident(incident["incident_id"])
        self.assertIsNotNone(saved)
        self.assertEqual(saved["status"], "REPORTED")
        self.assertEqual(saved["payload"]["status"], "REPORTED")
        self.assertEqual(len(self.store.get_audit(incident["incident_id"])), 1)
        self.assertEqual(
            self.table_counts(incident["incident_id"], incident["event_id"]),
            (1, 1, 1),
        )

        # After removing the synthetic fault, the same transition should succeed once.
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("DROP TRIGGER inject_transition_audit_failure")

        result = self.store.transition(
            incident["incident_id"],
            "ACKNOWLEDGED",
            actor_role="race_control",
            at="2026-10-28T02:01:00Z",
            correlation_id="corr_FAILURE_TRANSITION_01",
        )
        self.assertEqual(result["status"], "ACKNOWLEDGED")
        self.assertEqual(
            self.store.get_incident(incident["incident_id"])["status"],
            "ACKNOWLEDGED",
        )
        self.assertEqual(len(self.store.get_audit(incident["incident_id"])), 2)


if __name__ == "__main__":
    unittest.main()
