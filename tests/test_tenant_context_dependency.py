import unittest
from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.eduautomate_payment_api import require_api_identity
from src.registry_client import RegistryDenied, RegistryUnavailable, VerifiedTenantAuthority
from src.tenant_context_dependency import get_registry_client, get_verified_tenant

TENANT = "tn_f47ac10b-58cc-4372-a567-0e02b2c3d479"
USER = "usr_11111111-2222-3333-4444-555555555555"
OTHER_TENANT = "tn_99999999-0000-4000-8000-000000000999"


class FakeRegistryClient:
    def __init__(self, result=None, error=None):
        self.result = result or VerifiedTenantAuthority(
            tenant_id=TENANT, user_id=USER, role="STUDENT",
            verified_at=datetime(2026, 10, 23, 10, 0, tzinfo=timezone.utc),
        )
        self.error = error
        self.calls = []

    def verify_membership(self, context):
        self.calls.append(context)
        if self.error:
            raise self.error
        return self.result


class TenantContextDependencyTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()

        @self.app.get("/tenant")
        def tenant_route(tenant=Depends(get_verified_tenant)):
            return {"tenant_id": tenant.tenant_id, "user_id": tenant.user_id, "role": tenant.role}

        self.claims = {"tenant_id": TENANT, "user_id": USER, "sub": "subject-1", "role": "student"}
        self.registry = FakeRegistryClient()
        self.app.dependency_overrides[require_api_identity] = lambda: self.claims
        self.app.dependency_overrides[get_registry_client] = lambda: self.registry
        self.client = TestClient(self.app)

    def test_active_membership_returns_registry_verified_context(self):
        response = self.client.get("/tenant", headers={"X-Tenant-ID": TENANT})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"tenant_id": TENANT, "user_id": USER, "role": "STUDENT"})
        self.assertEqual(len(self.registry.calls), 1)

    def test_missing_tenant_header_fails_closed(self):
        response = self.client.get("/tenant")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "TENANT_CONTEXT_MISSING")
        self.assertEqual(self.registry.calls, [])

    def test_malformed_tenant_id_is_rejected_before_registry_call(self):
        response = self.client.get("/tenant", headers={"X-Tenant-ID": "invalid_tenant_12345"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "INVALID_TENANT_ID_FORMAT")
        self.assertEqual(self.registry.calls, [])

    def test_header_cannot_override_signed_tenant_claim(self):
        response = self.client.get("/tenant", headers={"X-Tenant-ID": OTHER_TENANT})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "TENANT_CONTEXT_MISMATCH")
        self.assertEqual(self.registry.calls, [])

    def test_missing_user_id_claim_fails_closed(self):
        self.claims.pop("user_id")
        response = self.client.get("/tenant", headers={"X-Tenant-ID": TENANT})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "AUTHENTICATED_USER_ID_MISSING")
        self.assertEqual(self.registry.calls, [])

    def test_registry_explicit_denial_returns_403(self):
        self.registry.error = RegistryDenied("synthetic denial")
        response = self.client.get("/tenant", headers={"X-Tenant-ID": TENANT})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "TENANT_MEMBERSHIP_DENIED")

    def test_registry_unavailable_returns_503(self):
        self.registry.error = RegistryUnavailable("synthetic outage")
        response = self.client.get("/tenant", headers={"X-Tenant-ID": TENANT})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "REGISTRY_UNAVAILABLE")

    def test_malformed_signed_user_id_returns_401(self):
        self.claims["user_id"] = "not-a-user-id"
        response = self.client.get("/tenant", headers={"X-Tenant-ID": TENANT})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "INVALID_AUTHENTICATED_USER_ID")


if __name__ == "__main__":
    unittest.main()
