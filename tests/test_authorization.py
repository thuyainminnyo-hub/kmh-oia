import unittest
from datetime import datetime, timedelta, timezone

from src.authorization import (
    AgentIdentity,
    AuthorizationRequest,
    DelegationGrant,
    PolicyDecisionPoint,
    PolicyRule,
    PrincipalIdentity,
)


NOW = datetime(2026, 11, 7, 8, 0, tzinfo=timezone.utc)


def principal(**changes):
    values = dict(
        subject="user:alice",
        tenant_id="tenant:one",
        issuer="https://identity.example",
        authenticated=True,
        active=True,
        authentication_method="oidc",
    )
    values.update(changes)
    return PrincipalIdentity(**values)


def agent(**changes):
    values = dict(
        subject="user:alice",
        issuer="https://identity.example",
        active=True,
    )
    values.update(changes)
    return AgentIdentity(**values)


def grant(**changes):
    values = dict(
        delegation_id="delegation:001",
        issuer_subject="user:alice",
        subject="agent:writer",
        tenant_id="tenant:one",
        audience="document.write",
        scopes=("write:document:123",),
        not_before=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        revoked=False,
    )
    values.update(changes)
    return DelegationGrant(**values)


def request(**changes):
    values = dict(
        request_id="request:001",
        principal=principal(),
        actor=agent(),
        tenant_id="tenant:one",
        action="read",
        resource="document:123",
        tool_name="document.read",
        policy_version="v1",
    )
    values.update(changes)
    return AuthorizationRequest(**values)


class PolicyDecisionPointTests(unittest.TestCase):
    def setUp(self):
        self.pdp = PolicyDecisionPoint(
            "v1",
            (
                PolicyRule("read", "document:123", "document.read"),
                PolicyRule("write", "document:123", "document.write", True),
            ),
        )

    def test_same_authenticated_principal_can_use_exact_rule(self):
        result = self.pdp.evaluate(request(), now=NOW)
        self.assertTrue(result.allowed)
        self.assertEqual(result.reason_code, "ALLOW")
        self.assertEqual(len(result.request_digest), 64)

    def test_missing_authentication_fails_closed(self):
        result = self.pdp.evaluate(request(principal=principal(authenticated=False)), now=NOW)
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason_code, "PRINCIPAL_NOT_AUTHENTICATED_OR_INACTIVE")

    def test_inactive_principal_fails_closed(self):
        result = self.pdp.evaluate(request(principal=principal(active=False)), now=NOW)
        self.assertFalse(result.allowed)

    def test_tenant_mismatch_fails_closed(self):
        result = self.pdp.evaluate(request(tenant_id="tenant:two"), now=NOW)
        self.assertEqual(result.reason_code, "TENANT_MISMATCH")

    def test_unknown_tool_or_resource_fails_closed(self):
        result = self.pdp.evaluate(request(tool_name="shell"), now=NOW)
        self.assertEqual(result.reason_code, "NO_UNIQUE_POLICY_RULE")

    def test_stale_policy_version_fails_closed(self):
        result = self.pdp.evaluate(request(policy_version="old"), now=NOW)
        self.assertEqual(result.reason_code, "POLICY_VERSION_MISMATCH")

    def test_delegation_required_for_distinct_agent(self):
        result = self.pdp.evaluate(
            request(actor=agent(subject="agent:writer", issuer="https://agents.example")),
            now=NOW,
        )
        self.assertEqual(result.reason_code, "DELEGATION_REQUIRED")

    def test_valid_delegation_is_allowed_for_exact_scope_and_audience(self):
        result = self.pdp.evaluate(
            request(
                action="write",
                tool_name="document.write",
                actor=agent(subject="agent:writer", issuer="https://agents.example"),
                delegation=grant(),
                approval_reference="human-approval:77",
            ),
            now=NOW,
        )
        self.assertTrue(result.allowed)

    def test_revoked_delegation_is_denied(self):
        result = self.pdp.evaluate(
            request(
                action="write", tool_name="document.write",
                actor=agent(subject="agent:writer", issuer="https://agents.example"),
                delegation=grant(revoked=True),
                approval_reference="human-approval:77",
            ),
            now=NOW,
        )
        self.assertEqual(result.reason_code, "DELEGATION_REVOKED")

    def test_expired_delegation_is_denied(self):
        result = self.pdp.evaluate(
            request(
                action="write", tool_name="document.write",
                actor=agent(subject="agent:writer", issuer="https://agents.example"),
                delegation=grant(expires_at=NOW),
                approval_reference="human-approval:77",
            ),
            now=NOW,
        )
        self.assertEqual(result.reason_code, "DELEGATION_OUTSIDE_VALIDITY_WINDOW")

    def test_cross_tenant_delegation_is_denied(self):
        result = self.pdp.evaluate(
            request(
                action="write", tool_name="document.write",
                actor=agent(subject="agent:writer", issuer="https://agents.example"),
                delegation=grant(tenant_id="tenant:two"),
                approval_reference="human-approval:77",
            ),
            now=NOW,
        )
        self.assertEqual(result.reason_code, "DELEGATION_TENANT_MISMATCH")

    def test_missing_delegated_scope_is_denied(self):
        result = self.pdp.evaluate(
            request(
                action="write", tool_name="document.write",
                actor=agent(subject="agent:writer", issuer="https://agents.example"),
                delegation=grant(scopes=("read:document:123",)),
                approval_reference="human-approval:77",
            ),
            now=NOW,
        )
        self.assertEqual(result.reason_code, "DELEGATION_SCOPE_MISSING")

    def test_human_approval_is_required_for_sensitive_rule(self):
        result = self.pdp.evaluate(
            request(
                action="write", tool_name="document.write",
                actor=agent(subject="agent:writer", issuer="https://agents.example"),
                delegation=grant(),
            ),
            now=NOW,
        )
        self.assertEqual(result.reason_code, "HUMAN_APPROVAL_REQUIRED")

    def test_naive_evaluation_time_fails_closed(self):
        result = self.pdp.evaluate(request(), now=datetime(2026, 11, 7, 8, 0))
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason_code, "INVALID_EVALUATION_TIME")

    def test_request_digest_changes_when_tool_changes(self):
        first = self.pdp.evaluate(request(), now=NOW)
        second = self.pdp.evaluate(request(tool_name="document.other"), now=NOW)
        self.assertNotEqual(first.request_digest, second.request_digest)

    def test_duplicate_matching_rules_fail_closed(self):
        pdp = PolicyDecisionPoint(
            "v1",
            (
                PolicyRule("read", "document:123", "document.read"),
                PolicyRule("read", "document:123", "document.read"),
            ),
        )
        result = pdp.evaluate(request(), now=NOW)
        self.assertEqual(result.reason_code, "NO_UNIQUE_POLICY_RULE")


if __name__ == "__main__":
    unittest.main()
