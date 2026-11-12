import unittest
import tempfile
from pathlib import Path

from src.execution_evidence import canonical_json, sha256_hex
from src.linked_evidence import (
    CallerEvidence,
    ReplayDetected,
    ServingEvidenceLedger,
    SQLiteServingEvidenceLedger,
    link_caller_and_admission,
)


class LinkedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            "method": "POST",
            "path": "/tools/payment",
            "body": {"amount": 1200, "currency": "MMK"},
        }
        self.call_digest = sha256_hex(canonical_json(self.request))
        self.caller = CallerEvidence(
            request_id="req-1",
            caller_agent_id="agent-1",
            caller_receipt_digest="c" * 64,
            call_digest=self.call_digest,
        )
        self.ledger = ServingEvidenceLedger("gateway-prod")

    def test_serving_party_records_and_links_independent_admission(self):
        admission = self.ledger.admit(
            caller=self.caller, actual_request=self.request,
            decision="deny", reason_code="approval-required",
            occurred_at_epoch=100,
        )
        linked = link_caller_and_admission(
            caller=self.caller, admission=admission,
            actual_request=self.request,
        )
        self.assertIsNotNone(linked)
        self.assertTrue(self.ledger.verify_chain())


    def test_sqlite_ledger_persists_and_verifies_after_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "serving.sqlite3"
            ledger = SQLiteServingEvidenceLedger(path, "gateway-prod")
            first = ledger.admit(
                caller=self.caller, actual_request=self.request,
                decision="deny", reason_code="approval-required", occurred_at_epoch=100,
            )
            self.assertEqual(first.sequence, 1)
            self.assertTrue(ledger.verify_chain())
            ledger.close()
            reopened = SQLiteServingEvidenceLedger(path, "gateway-prod")
            self.assertEqual(len(reopened.receipts), 1)
            self.assertTrue(reopened.verify_chain())
            reopened.close()

    def test_sqlite_ledger_rejects_replay_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "serving.sqlite3"
            ledger = SQLiteServingEvidenceLedger(path, "gateway-prod")
            ledger.admit(
                caller=self.caller, actual_request=self.request,
                decision="allow", reason_code="ok", occurred_at_epoch=100,
            )
            ledger.close()
            reopened = SQLiteServingEvidenceLedger(path, "gateway-prod")
            with self.assertRaises(ReplayDetected):
                reopened.admit(
                    caller=self.caller, actual_request=self.request,
                    decision="allow", reason_code="ok", occurred_at_epoch=101,
                )
            reopened.close()

    def test_sqlite_ledger_triggers_reject_update_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = SQLiteServingEvidenceLedger(
                Path(directory) / "serving.sqlite3", "gateway-prod"
            )
            ledger.admit(
                caller=self.caller, actual_request=self.request,
                decision="deny", reason_code="policy-denied", occurred_at_epoch=100,
            )
            with self.assertRaises(Exception):
                ledger._db.execute(
                    "UPDATE serving_receipts SET decision='allow' WHERE sequence=1"
                )
            with self.assertRaises(Exception):
                ledger._db.execute("DELETE FROM serving_receipts WHERE sequence=1")
            self.assertTrue(ledger.verify_chain())
            ledger.close()

    def test_serving_party_recomputes_request_digest(self):
        changed = {**self.request, "body": {"amount": 12000, "currency": "MMK"}}
        with self.assertRaises(ValueError):
            self.ledger.admit(
                caller=self.caller, actual_request=changed,
                decision="allow", reason_code="ok", occurred_at_epoch=100,
            )

    def test_duplicate_caller_receipt_reference_is_rejected(self):
        self.ledger.admit(
            caller=self.caller, actual_request=self.request,
            decision="allow", reason_code="ok", occurred_at_epoch=100,
        )
        with self.assertRaises(ReplayDetected):
            self.ledger.admit(
                caller=self.caller, actual_request=self.request,
                decision="allow", reason_code="ok", occurred_at_epoch=101,
            )

    def test_link_rejects_cross_request_or_agent_substitution(self):
        admission = self.ledger.admit(
            caller=self.caller, actual_request=self.request,
            decision="allow", reason_code="ok", occurred_at_epoch=100,
        )
        other = CallerEvidence(
            request_id="req-other", caller_agent_id="agent-1",
            caller_receipt_digest=self.caller.caller_receipt_digest,
            call_digest=self.call_digest,
        )
        self.assertIsNone(link_caller_and_admission(
            caller=other, admission=admission, actual_request=self.request,
        ))

    def test_denied_decision_is_still_recorded(self):
        admission = self.ledger.admit(
            caller=self.caller, actual_request=self.request,
            decision="deny", reason_code="policy-denied",
            occurred_at_epoch=100,
        )
        self.assertEqual(admission.decision, "deny")
        self.assertEqual(len(self.ledger.receipts), 1)


if __name__ == "__main__":
    unittest.main()
