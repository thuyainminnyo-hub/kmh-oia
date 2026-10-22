import os
import tempfile
import unittest
from fastapi.testclient import TestClient

from src.eduautomate_payment_api import app


class EduAutomatePaymentApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = os.environ.get("EDUAUTOMATE_DB_PATH")
        self.old_admin = os.environ.get("EDUAUTOMATE_ADMIN_TOKEN")
        os.environ["EDUAUTOMATE_DB_PATH"] = os.path.join(self.tmp.name, "payments.sqlite3")
        os.environ.pop("EDUAUTOMATE_ADMIN_TOKEN", None)
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        if self.old_db is None:
            os.environ.pop("EDUAUTOMATE_DB_PATH", None)
        else:
            os.environ["EDUAUTOMATE_DB_PATH"] = self.old_db
        if self.old_admin is None:
            os.environ.pop("EDUAUTOMATE_ADMIN_TOKEN", None)
        else:
            os.environ["EDUAUTOMATE_ADMIN_TOKEN"] = self.old_admin
        self.tmp.cleanup()

    def create(self, key="test-key-0001", amount=18000000):
        return self.client.post(
            "/v1/payments",
            headers={"Idempotency-Key": key},
            json={"student_id": "stu_test", "amount_minor": amount, "currency": "MMK", "purpose": "course_fee"},
        )

    def admin_decide(self, payment_id, decision="confirm", token="test-admin-secret"):
        os.environ["EDUAUTOMATE_ADMIN_TOKEN"] = token
        return self.client.post(
            f"/v1/payments/{payment_id}/admin-decision",
            headers={"X-Admin-Token": token, "X-Actor-Id": "admin-test-1"},
            json={"decision": decision, "note": "Checked transfer reference against records"},
        )

    def test_create_pending_and_get(self):
        created = self.create()
        self.assertEqual(created.status_code, 201)
        body = created.json()
        self.assertEqual(body["status"], "pending")
        fetched = self.client.get(f"/v1/payments/{body['payment_id']}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["payment_id"], body["payment_id"])

    def test_repeated_idempotency_key_same_payload_returns_same_record(self):
        first = self.create()
        second = self.create()
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["payment_id"], second.json()["payment_id"])

    def test_reused_idempotency_key_different_payload_conflicts(self):
        self.create()
        conflict = self.create(amount=100)
        self.assertEqual(conflict.status_code, 409)

    def test_create_rejects_nonpositive_amount(self):
        result = self.create(amount=0)
        self.assertEqual(result.status_code, 422)

    def test_unknown_payment_is_not_found(self):
        self.assertEqual(self.client.get("/v1/payments/pay_unknown").status_code, 404)

    def test_admin_decision_fails_closed_without_configured_token(self):
        created = self.create().json()
        result = self.admin_decide(created["payment_id"])
        self.assertEqual(result.status_code, 503)
        self.assertEqual(self.client.get(f"/v1/payments/{created['payment_id']}").json()["status"], "pending")

    def test_admin_decision_rejects_wrong_token(self):
        created = self.create().json()
        os.environ["EDUAUTOMATE_ADMIN_TOKEN"] = "right-secret"
        result = self.client.post(
            f"/v1/payments/{created['payment_id']}/admin-decision",
            headers={"X-Admin-Token": "wrong-secret", "X-Actor-Id": "admin-test-1"},
            json={"decision": "confirm", "note": "checked reference"},
        )
        self.assertEqual(result.status_code, 401)
        self.assertEqual(self.client.get(f"/v1/payments/{created['payment_id']}").json()["status"], "pending")

    def test_confirm_only_pending_and_audits_actor(self):
        created = self.create().json()
        decided = self.admin_decide(created["payment_id"])
        self.assertEqual(decided.status_code, 200)
        self.assertEqual(decided.json()["status"], "confirmed")
        self.assertEqual(decided.json()["confirmed_by"], "admin-test-1")
        repeated = self.admin_decide(created["payment_id"])
        self.assertEqual(repeated.status_code, 409)

    def test_rejection_keeps_record_not_confirmed(self):
        created = self.create().json()
        rejected = self.admin_decide(created["payment_id"], decision="reject")
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.json()["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
