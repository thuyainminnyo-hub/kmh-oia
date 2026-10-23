import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import httpx
from pydantic import ValidationError

from src.registry_client import REGISTRY_VERIFY_PATH, RegistryClient, RegistryDenied, RegistryUnavailable, TenantContext

TENANT = "tn_f47ac10b-58cc-4372-a567-0e02b2c3d479"
USER = "usr_11111111-2222-3333-4444-555555555555"
OTHER_USER = "usr_88888888-8888-8888-8888-888888888888"


def response_body(tenant_id=TENANT, user_id=USER, status="ACTIVE", membership_status="ACTIVE"):
    return {"tenant_id": tenant_id, "status": status, "membership": {"user_id": user_id, "role": "STUDENT",
            "status": membership_status, "verified_at": "2026-10-23T10:00:00Z"}}


class RegistryClientTests(unittest.TestCase):
    def client_for(self, status_code=200, body=None, *, exception=None):
        def handler(request):
            self.assertEqual(str(request.url), "https://registry.test" + REGISTRY_VERIFY_PATH)
            self.assertEqual(request.headers["Authorization"], "Bearer synthetic-service-token")
            self.assertEqual(request.headers["Content-Type"], "application/json")
            self.assertEqual(json.loads(request.content), {"tenant_id": TENANT, "user_id": USER})
            if exception:
                raise exception
            return httpx.Response(status_code, json=body if body is not None else {})
        return RegistryClient(base_url="https://registry.test/", service_token="synthetic-service-token",
                              timeout_seconds=0.5, transport=httpx.MockTransport(handler))

    def context(self):
        return TenantContext(tenant_id=TENANT, user_id=USER)

    def test_valid_active_tenant_and_member_allows(self):
        result = self.client_for(body=response_body()).verify_membership(self.context())
        self.assertEqual((result.tenant_id, result.user_id, result.role), (TENANT, USER, "STUDENT"))
        self.assertEqual(result.verified_at, datetime(2026, 10, 23, 10, 0, tzinfo=timezone.utc))

    def test_deactivated_tenant_denied(self):
        with self.assertRaises(RegistryDenied):
            self.client_for(body=response_body(status="DEACTIVATED")).verify_membership(self.context())

    def test_revoked_membership_denied(self):
        with self.assertRaises(RegistryDenied):
            self.client_for(body=response_body(membership_status="REVOKED")).verify_membership(self.context())

    def test_404_and_403_are_denied(self):
        for code in (403, 404):
            with self.subTest(status_code=code), self.assertRaises(RegistryDenied):
                self.client_for(status_code=code).verify_membership(self.context())

    def test_503_and_unexpected_status_fail_closed(self):
        for code in (401, 429, 500, 503):
            with self.subTest(status_code=code), self.assertRaises(RegistryUnavailable):
                self.client_for(status_code=code).verify_membership(self.context())

    def test_timeout_fails_closed(self):
        with self.assertRaises(RegistryUnavailable):
            self.client_for(exception=httpx.ReadTimeout("synthetic timeout")).verify_membership(self.context())

    def test_transport_error_fails_closed(self):
        with self.assertRaises(RegistryUnavailable):
            self.client_for(exception=httpx.ConnectError("synthetic failure")).verify_membership(self.context())

    def test_wrong_tenant_or_user_in_success_response_denied(self):
        for body in (response_body(tenant_id="tn_99999999-0000-4000-8000-000000000999"), response_body(user_id=OTHER_USER)):
            with self.subTest(body=body), self.assertRaises(RegistryDenied):
                self.client_for(body=body).verify_membership(self.context())

    def test_malformed_or_incomplete_200_fails_closed(self):
        for body in ({}, {"tenant_id": TENANT, "status": "ACTIVE", "membership": None}):
            with self.subTest(body=body), self.assertRaises(RegistryUnavailable):
                self.client_for(body=body).verify_membership(self.context())

    def test_missing_configuration_fails_closed_without_network(self):
        with patch("src.registry_client.httpx.Client") as client:
            with self.assertRaises(RegistryUnavailable):
                RegistryClient(base_url="", service_token="").verify_membership(self.context())
            client.assert_not_called()

    def test_malformed_tenant_id_rejected_before_request(self):
        with self.assertRaises(ValidationError):
            TenantContext(tenant_id="invalid_tenant_12345", user_id=USER)

    def test_tenant_id_must_be_canonical_uuid4(self):
        with self.assertRaises(ValidationError):
            TenantContext(tenant_id="tn_f47ac10b-58cc-3372-a567-0e02b2c3d479", user_id=USER)


if __name__ == "__main__":
    unittest.main()
