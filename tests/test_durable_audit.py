import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.agent_trust import AuditEvent
from src.durable_audit import SQLiteHashChainAudit


class SQLiteHashChainAuditTests(unittest.TestCase):
    def event(self, sequence, request_id=None):
        return AuditEvent(
            sequence=sequence,
            request_id=request_id or f"req-{sequence}",
            agent_id="agent-1",
            tool_name="read",
            resource="docs/item",
            decision="allow",
            reason="authorized",
        )

    def test_persists_events_and_verifies_chain_after_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.sqlite3"
            audit = SQLiteHashChainAudit(path)
            audit.append(self.event(1))
            audit.append(self.event(2))
            audit.close()

            reopened = SQLiteHashChainAudit(path)
            self.assertEqual([item.request_id for item in reopened.events], ["req-1", "req-2"])
            self.assertTrue(reopened.verify_chain())
            reopened.close()

    def test_rejects_non_contiguous_sequence(self):
        with tempfile.TemporaryDirectory() as directory:
            audit = SQLiteHashChainAudit(Path(directory) / "audit.sqlite3")
            with self.assertRaises(ValueError):
                audit.append(self.event(2))
            self.assertEqual(audit.events, ())
            audit.close()

    def test_database_triggers_reject_update_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            audit = SQLiteHashChainAudit(Path(directory) / "audit.sqlite3")
            audit.append(self.event(1))
            with self.assertRaises(sqlite3.IntegrityError):
                audit._connection.execute(
                    "UPDATE audit_events SET event_json='{}' WHERE sequence=1"
                )
            with self.assertRaises(sqlite3.IntegrityError):
                audit._connection.execute("DELETE FROM audit_events WHERE sequence=1")
            self.assertTrue(audit.verify_chain())
            audit.close()

    def test_verifier_detects_tampered_row_if_triggers_are_bypassed(self):
        with tempfile.TemporaryDirectory() as directory:
            audit = SQLiteHashChainAudit(Path(directory) / "audit.sqlite3")
            audit.append(self.event(1))
            audit._connection.execute("DROP TRIGGER audit_events_no_update")
            audit._connection.execute(
                "UPDATE audit_events SET event_json='{}' WHERE sequence=1"
            )
            self.assertFalse(audit.verify_chain())
            audit.close()


if __name__ == "__main__":
    unittest.main()
