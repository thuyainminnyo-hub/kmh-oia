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
        self.old_api = os.environ.get("EDUAUTOMATE_API_TOKEN")
        self.old_actor = os.environ.get("EDUAUTOMATE_ADMIN_ACTOR_ID")
        os.environ["EDUAUTOMATE_ADMIN_ACTOR_ID"] = "admin-test-1"
        os.environ["EDUAUTOMATE_DB_PATH"] = os.path.join(self.tmp.name, "payments.sqlite3")
        os.environ["EDUAUTOMATE_API_TOKEN"] = "test-api-secret"
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
        if self.old_api is None:
            os.environ.pop("EDUAUTOMATE_API_TOKEN", None)
        else:
            os.environ["EDUAUTOMATE_API_TOKEN"] = self.old_api
        if self.old_actor is None:
            os.environ.pop("EDUAUTOMATE_ADMIN_ACTOR_ID", None)
        else:
            os.environ["EDUAUTOMATE_ADMIN_ACTOR_ID"] = self.old_actor
        self.tmp.cleanup()

    def create(self, key="test-key-0001", amount=18000000):
        return self.client.post(
            "/v1/payments",
            headers={"Idempotency-Key": key, "X-API-Token": "test-api-secret"},
            json={"student_id": "stu_test", "amount_minor": amount, "currency": "MMK", "purpose": "course_fee"},
        )

    def admin_decide(self, payment_id, decision="confirm", token="test-admin-secret", evidence_reference="private-evidence-ref-001"):
        os.environ["EDUAUTOMATE_ADMIN_TOKEN"] = token
        return self.client.post(
            "/v1/payments/{}/admin-decision".format(payment_id),
            headers={"X-Admin-Token": token},
            json={
                "decision": decision,
                "note": "Checked transfer reference against records",
                "evidence_reference": evidence_reference if decision == "confirm" else None,
            },
        )

    def get(self, payment_id):
        return self.client.get(
            "/v1/payments/{}".format(payment_id),
            headers={"X-API-Token": "test-api-secret"},
        )

    def test_create_pending_and_get(self):
        created = self.create()
        self.assertEqual(created.status_code, 201)
        body = created.json()
        self.assertEqual(body["status"], "pending")
        fetched = self.get(body["payment_id"])
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
        self.assertEqual(self.get("pay_unknown").status_code, 404)

    def test_api_requires_configured_token_and_rejects_bad_token(self):
        os.environ.pop("EDUAUTOMATE_API_TOKEN", None)
        missing = self.client.post(
            "/v1/payments",
            headers={"Idempotency-Key": "missing-api-1"},
            json={"student_id": "stu_test", "amount_minor": 100, "currency": "MMK", "purpose": "course_fee"},
        )
        self.assertEqual(missing.status_code, 503)
        os.environ["EDUAUTOMATE_API_TOKEN"] = "right-api-token"
        wrong = self.client.post(
            "/v1/payments",
            headers={"Idempotency-Key": "wrong-api-1", "X-API-Token": "wrong-token"},
            json={"student_id": "stu_test", "amount_minor": 100, "currency": "MMK", "purpose": "course_fee"},
        )
        self.assertEqual(wrong.status_code, 401)

    def test_admin_decision_fails_closed_without_configured_token(self):
        created = self.create().json()
        os.environ.pop("EDUAUTOMATE_ADMIN_TOKEN", None)
        result = self.client.post(
            "/v1/payments/{}/admin-decision".format(created["payment_id"]),
            headers={"X-Admin-Token": "test-admin-secret"},
            json={
                "decision": "confirm",
                "note": "Checked transfer reference against records",
                "evidence_reference": "private-evidence-ref-001",
            },
        )
        self.assertEqual(result.status_code, 503)
        self.assertEqual(self.get(created["payment_id"]).json()["status"], "pending")

    def test_admin_decision_rejects_wrong_token(self):
        created = self.create().json()
        os.environ["EDUAUTOMATE_ADMIN_TOKEN"] = "right-secret"
        result = self.client.post(
            "/v1/payments/{}/admin-decision".format(created["payment_id"]),
            headers={"X-Admin-Token": "wrong-secret"},
            json={"decision": "confirm", "note": "checked reference", "evidence_reference": "ref-123"},
        )
        self.assertEqual(result.status_code, 401)
        self.assertEqual(self.get(created["payment_id"]).json()["status"], "pending")

    def test_admin_confirm_requires_opaque_evidence_reference(self):
        created = self.create().json()
        result = self.admin_decide(created["payment_id"], evidence_reference=None)
        self.assertEqual(result.status_code, 422)
        self.assertEqual(self.get(created["payment_id"]).json()["status"], "pending")

    def test_confirm_only_pending_and_audits_actor_and_reference(self):
        created = self.create().json()
        decided = self.admin_decide(created["payment_id"])
        self.assertEqual(decided.status_code, 200)
        self.assertEqual(decided.json()["status"], "confirmed")
        self.assertEqual(decided.json()["confirmed_by"], "admin-test-1")
        self.assertEqual(decided.json()["evidence_reference"], "private-evidence-ref-001")
        repeated = self.admin_decide(created["payment_id"])
        self.assertEqual(repeated.status_code, 409)

    def test_rejection_keeps_record_not_confirmed(self):
        created = self.create().json()
        rejected = self.admin_decide(created["payment_id"], decision="reject")
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.json()["status"], "rejected")
        self.assertIsNone(rejected.json()["confirmed_by"])


if __name__ == "__main__":
    unittest.main()
