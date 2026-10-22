import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.eduautomate_payment_api import app, connect_db


def make_identity_token(claims, secret="identity-test-secret"):
    def enc(obj):
        raw = json.dumps(obj, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")
    header = enc({"alg": "HS256", "typ": "JWT"})
    payload = enc(claims)
    signed = f"{header}.{payload}".encode("ascii")
    sig = base64.urlsafe_b64encode(hmac.new(secret.encode(), signed, hashlib.sha256).digest()).decode().rstrip("=")
    return f"{header}.{payload}.{sig}"


class EduAutomatePaymentApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.previous_env = {key: os.environ.get(key) for key in (
            "EDUAUTOMATE_DB_PATH", "EDUAUTOMATE_ADMIN_TOKEN", "EDUAUTOMATE_API_TOKEN",
            "EDUAUTOMATE_ADMIN_ACTOR_ID", "EDUAUTOMATE_AUTH_MODE",
            "EDUAUTOMATE_SHARED_TOKEN_PROTOTYPE_ENABLED",
            "EDUAUTOMATE_IDENTITY_HS256_SECRET", "EDUAUTOMATE_IDENTITY_ISSUER",
            "EDUAUTOMATE_IDENTITY_AUDIENCE", "EDUAUTOMATE_ENV",
        )}
        os.environ["EDUAUTOMATE_ADMIN_ACTOR_ID"] = "admin-test-1"
        os.environ["EDUAUTOMATE_DB_PATH"] = os.path.join(self.tmp.name, "payments.sqlite3")
        os.environ["EDUAUTOMATE_API_TOKEN"] = "test-api-secret"
        os.environ["EDUAUTOMATE_ADMIN_TOKEN"] = "test-admin-secret"
        os.environ["EDUAUTOMATE_AUTH_MODE"] = "shared_token"
        os.environ["EDUAUTOMATE_SHARED_TOKEN_PROTOTYPE_ENABLED"] = "true"
        os.environ["EDUAUTOMATE_IDENTITY_HS256_SECRET"] = "identity-test-secret"
        os.environ["EDUAUTOMATE_IDENTITY_ISSUER"] = "https://issuer.test"
        os.environ["EDUAUTOMATE_IDENTITY_AUDIENCE"] = "eduautomate-test"
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for key, value in self.previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def identity_headers(self, sub, student_id, tenant_id="tenant-a", role="student", exp=None):
        claims = {
            "iss": "https://issuer.test", "aud": "eduautomate-test",
            "sub": sub, "student_id": student_id, "tenant_id": tenant_id,
            "role": role, "exp": exp or int(time.time()) + 300,
        }
        return {"Authorization": "Bearer " + make_identity_token(claims)}

    def test_production_mode_disables_generated_api_documentation(self):
        env = dict(os.environ)
        env["EDUAUTOMATE_ENV"] = "production"
        code = (
            "from src.eduautomate_payment_api import app; "
            "assert app.docs_url is None; "
            "assert app.redoc_url is None; "
            "assert app.openapi_url is None; "
            "assert not any(getattr(route, 'path', None) in "
            "{'/docs', '/redoc', '/openapi.json'} for route in app.routes)"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            env=env, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

    def test_healthz_is_liveness_only_and_does_not_initialize_database(self):
        with patch("src.eduautomate_payment_api.init_db") as initialize_db:
            response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        initialize_db.assert_not_called()

    def create(self, key="test-key-0001", amount=18000000):
        return self.client.post(
            "/v1/payments",
            headers={"Idempotency-Key": key, "X-API-Token": "test-api-secret"},
            json={"student_id": "stu_test", "amount_minor": amount, "currency": "MMK", "purpose": "course_fee"},
        )

    def admin_decide(self, payment_id, decision="confirm", token="test-admin-secret", evidence_reference="private-evidence-ref-001"):
        os.environ["EDUAUTOMATE_ADMIN_TOKEN"] = token
        return self.client.post(
            f"/v1/payments/{payment_id}/admin-decision",
            headers={"X-Admin-Token": token},
            json={"decision": decision, "note": "Checked transfer reference against records",
                  "evidence_reference": evidence_reference if decision == "confirm" else None},
        )

    def get(self, payment_id):
        return self.client.get(f"/v1/payments/{payment_id}", headers={"X-API-Token": "test-api-secret"})

    def test_create_pending_and_get(self):
        created = self.create()
        self.assertEqual(created.status_code, 201)
        body = created.json()
        self.assertEqual(body["status"], "pending")
        fetched = self.get(body["payment_id"])
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["payment_id"], body["payment_id"])

    def test_repeated_idempotency_key_same_payload_returns_same_record(self):
        first, second = self.create(), self.create()
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["payment_id"], second.json()["payment_id"])

    def test_reused_idempotency_key_different_payload_conflicts(self):
        self.create()
        self.assertEqual(self.create(amount=100).status_code, 409)

    def test_create_rejects_nonpositive_amount(self):
        self.assertEqual(self.create(amount=0).status_code, 422)

    def test_create_rejects_boolean_amount(self):
        response = self.client.post(
            "/v1/payments",
            headers={"Idempotency-Key": "boolean-amount-1", "X-API-Token": "test-api-secret"},
            json={"student_id": "stu_test", "amount_minor": True, "currency": "MMK", "purpose": "course_fee"},
        )
        self.assertEqual(response.status_code, 422)

    def test_unknown_payment_is_not_found(self):
        self.assertEqual(self.get("pay_unknown").status_code, 404)

    def test_payment_read_requires_api_token(self):
        created = self.create().json()
        self.assertEqual(self.client.get(f"/v1/payments/{created['payment_id']}").status_code, 401)

    def test_shared_token_read_fails_closed_without_explicit_prototype_opt_in(self):
        created = self.create().json()
        os.environ.pop("EDUAUTOMATE_SHARED_TOKEN_PROTOTYPE_ENABLED", None)
        with patch("src.eduautomate_payment_api._get_record_by_id") as record_lookup:
            response = self.get(created["payment_id"])
        self.assertEqual(response.status_code, 503)
        record_lookup.assert_not_called()

    def test_api_requires_configured_token_and_rejects_bad_token(self):
        os.environ.pop("EDUAUTOMATE_API_TOKEN", None)
        missing = self.client.post("/v1/payments", headers={"Idempotency-Key": "missing-api-1"},
            json={"student_id": "stu_test", "amount_minor": 100, "currency": "MMK", "purpose": "course_fee"})
        self.assertEqual(missing.status_code, 503)
        os.environ["EDUAUTOMATE_API_TOKEN"] = "right-api-token"
        wrong = self.client.post("/v1/payments", headers={"Idempotency-Key": "wrong-api-1", "X-API-Token": "wrong-token"},
            json={"student_id": "stu_test", "amount_minor": 100, "currency": "MMK", "purpose": "course_fee"})
        self.assertEqual(wrong.status_code, 401)

    def test_admin_decision_fails_closed_without_configured_token(self):
        created = self.create().json()
        os.environ.pop("EDUAUTOMATE_ADMIN_TOKEN", None)
        response = self.client.post(f"/v1/payments/{created['payment_id']}/admin-decision",
            headers={"X-Admin-Token": "test-admin-secret"},
            json={"decision": "confirm", "note": "Checked transfer reference against records",
                  "evidence_reference": "private-evidence-ref-001"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.get(created["payment_id"]).json()["status"], "pending")

    def test_admin_decision_rejects_wrong_token(self):
        created = self.create().json()
        response = self.client.post(f"/v1/payments/{created['payment_id']}/admin-decision",
            headers={"X-Admin-Token": "wrong-secret"},
            json={"decision": "confirm", "note": "checked reference", "evidence_reference": "ref-123"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.get(created["payment_id"]).json()["status"], "pending")

    def test_admin_confirm_requires_opaque_evidence_reference(self):
        created = self.create().json()
        response = self.admin_decide(created["payment_id"], evidence_reference=None)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.get(created["payment_id"]).json()["status"], "pending")

    def test_admin_confirm_rejects_url_like_evidence_references(self):
        created = self.create().json()
        for value in ("https://example.invalid/public-slip.jpg", "ftp://example.invalid/public-slip.jpg",
                      "//example.invalid/public-slip.jpg", "www.example.invalid/public-slip.jpg"):
            with self.subTest(evidence_reference=value):
                self.assertEqual(self.admin_decide(created["payment_id"], evidence_reference=value).status_code, 422)

    def test_admin_decision_requires_server_configured_actor(self):
        created = self.create().json()
        os.environ.pop("EDUAUTOMATE_ADMIN_ACTOR_ID", None)
        response = self.client.post(f"/v1/payments/{created['payment_id']}/admin-decision",
            headers={"X-Admin-Token": "test-admin-secret"},
            json={"decision": "confirm", "note": "Checked transfer reference against records",
                  "evidence_reference": "private-evidence-ref-001"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.get(created["payment_id"]).json()["status"], "pending")

    def test_confirm_only_pending_and_audits_actor_and_reference(self):
        created = self.create().json()
        decided = self.admin_decide(created["payment_id"])
        self.assertEqual(decided.status_code, 200)
        self.assertEqual(decided.json()["status"], "confirmed")
        self.assertEqual(decided.json()["confirmed_by"], "admin-test-1")
        self.assertEqual(decided.json()["evidence_reference"], "private-evidence-ref-001")
        self.assertEqual(self.admin_decide(created["payment_id"]).status_code, 409)

    def test_rejection_keeps_record_not_confirmed(self):
        created = self.create().json()
        rejected = self.admin_decide(created["payment_id"], decision="reject")
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.json()["status"], "rejected")
        self.assertIsNone(rejected.json()["confirmed_by"])

    def test_shared_token_writes_fail_closed_without_explicit_prototype_opt_in(self):
        os.environ.pop("EDUAUTOMATE_SHARED_TOKEN_PROTOTYPE_ENABLED", None)
        response = self.create(key="prototype-opt-in-required")
        self.assertEqual(response.status_code, 503)
        with connect_db() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM payments WHERE idempotency_key=?",
                ("prototype-opt-in-required",),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_identity_mode_fails_closed_for_unsafe_create_without_tenant_schema(self):
        os.environ["EDUAUTOMATE_AUTH_MODE"] = "identity"
        response = self.client.post("/v1/payments", headers={
            "Authorization": "Bearer " + make_identity_token({
                "iss":"https://issuer.test","aud":"eduautomate-test","sub":"stu-a",
                "student_id":"stu-a","tenant_id":"tenant-a","role":"student","exp":int(time.time())+300
            }),
            "Idempotency-Key": "identity-mode-001", "X-API-Token": "test-api-secret"
        }, json={"student_id":"stu-a","amount_minor":100,"currency":"MMK","purpose":"course_fee"})
        self.assertEqual(response.status_code, 503)
        with connect_db() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM payments WHERE idempotency_key=?",
                ("identity-mode-001",),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_identity_mode_disables_reads_until_tenant_scope_is_persisted(self):
        created = self.create().json()
        os.environ["EDUAUTOMATE_AUTH_MODE"] = "identity"
        for tenant_id, student_id, role in (
            ("tenant-a", "stu_test", "student"),
            ("tenant-b", "stu-other", "student"),
            ("tenant-a", "admin-1", "payment_admin"),
        ):
            with self.subTest(tenant_id=tenant_id, student_id=student_id, role=role):
                response = self.client.get(
                    f"/v1/payments/{created['payment_id']}",
                    headers=self.identity_headers("subject-1", student_id, tenant_id, role),
                )
                self.assertEqual(response.status_code, 503)

    def test_identity_mode_denies_before_payment_lookup(self):
        os.environ["EDUAUTOMATE_AUTH_MODE"] = "identity"
        with patch("src.eduautomate_payment_api._get_record_by_id") as record_lookup:
            response = self.client.get(
                "/v1/payments/pay_synthetic",
                headers=self.identity_headers("subject-1", "stu-test", "tenant-a", "student"),
            )
        self.assertEqual(response.status_code, 503)
        record_lookup.assert_not_called()

    def test_identity_mode_rejects_invalid_or_expired_assertion_for_reads(self):
        created = self.create().json()
        os.environ["EDUAUTOMATE_AUTH_MODE"] = "identity"
        headers = {"X-API-Token":"test-api-secret","Authorization":"Bearer " + make_identity_token({
            "iss":"https://issuer.test","aud":"eduautomate-test","sub":"stu-a",
            "student_id":"stu-a","tenant_id":"tenant-a","role":"student","exp":int(time.time())-10
        })}
        with patch("src.eduautomate_payment_api._get_record_by_id") as record_lookup, patch(
            "src.eduautomate_payment_api.init_db"
        ) as init_db, patch("src.eduautomate_payment_api.connect_db") as connect_db:
            response = self.client.get("/v1/payments/" + created["payment_id"], headers=headers)
        self.assertEqual(response.status_code, 401)
        record_lookup.assert_not_called()
        init_db.assert_not_called()
        connect_db.assert_not_called()
    def test_shared_token_admin_decision_fails_closed_without_explicit_prototype_opt_in(self):
        created = self.create(key="admin-prototype-opt-in").json()
        os.environ.pop("EDUAUTOMATE_SHARED_TOKEN_PROTOTYPE_ENABLED", None)
        response = self.admin_decide(created["payment_id"])
        self.assertEqual(response.status_code, 503)
        with connect_db() as conn:
            row = conn.execute(
                "SELECT status FROM payments WHERE payment_id=?",
                (created["payment_id"],),
            ).fetchone()
        self.assertEqual(row["status"], "pending")

    def test_identity_mode_admin_denial_happens_before_database_access(self):
        created = self.create(key="identity-admin-no-db").json()
        os.environ["EDUAUTOMATE_AUTH_MODE"] = "identity"
        with patch("src.eduautomate_payment_api.init_db") as init_db, patch(
            "src.eduautomate_payment_api.connect_db"
        ) as connect_db:
            response = self.client.post(
                f"/v1/payments/{created['payment_id']}/admin-decision",
                headers=self.identity_headers(
                    "admin-subject", "admin-1", "tenant-a", "payment_admin"
                ),
                json={
                    "decision": "confirm",
                    "note": "synthetic test",
                    "evidence_reference": "private-evidence-ref-002",
                },
            )
        self.assertEqual(response.status_code, 503)
        init_db.assert_not_called()
        connect_db.assert_not_called()

    def test_identity_mode_admin_decisions_fail_closed_until_verified_adapter_and_schema_exist(self):
        created = self.create().json()
        os.environ["EDUAUTOMATE_AUTH_MODE"] = "identity"
        response = self.client.post(f"/v1/payments/{created['payment_id']}/admin-decision",
            headers={"Authorization":"Bearer " + make_identity_token({
                "iss":"https://issuer.test","aud":"eduautomate-test","sub":"admin-1",
                "student_id":"admin-1","tenant_id":"tenant-a","role":"payment_admin","exp":int(time.time())+300
            })},
            json={"decision":"confirm","note":"Checked transfer reference against records",
                  "evidence_reference":"private-evidence-ref-001"})
        self.assertEqual(response.status_code, 503)
        with connect_db() as conn:
            row = conn.execute(
                "SELECT status FROM payments WHERE payment_id=?",
                (created["payment_id"],),
            ).fetchone()
        self.assertEqual(row["status"], "pending")


if __name__ == "__main__":
    unittest.main()
