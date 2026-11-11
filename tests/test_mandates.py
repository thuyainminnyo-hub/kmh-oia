import hashlib
import unittest

from src.mandates import (
    InMemoryNonceStore,
    MandateValidator,
    SignedMandate,
    TaskMandate,
)


class DigestOnlyTestVerifier:
    """Test fixture only; SHA-256 is not a production signature algorithm."""

    def verify(self, *, key_id, message, signature):
        return key_id == "test-key" and signature == hashlib.sha256(message).digest()


class MandateValidatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = MandateValidator(
            DigestOnlyTestVerifier(), InMemoryNonceStore(),
            max_lifetime_seconds=900, max_delegation_depth=3,
        )
        self.mandate = TaskMandate(
            mandate_id="m-root",
            issuer="org-owner",
            subject_agent_id="agent-1",
            actor_workload_id="spiffe://kmh.test/agent-1",
            task_id="task-1",
            audience="kmh-tool-gateway",
            scopes=frozenset({"tool:read", "tool:write"}),
            resources=frozenset({"document:123", "document:456"}),
            issued_at=100,
            not_before=100,
            expires_at=500,
            nonce="nonce-root-1",
            key_id="test-key",
            max_delegation_depth=2,
        )

    def signed(self, mandate):
        signature = hashlib.sha256(mandate.canonical_payload()).digest()
        return SignedMandate(mandate, signature)

    def validate(self, signed=None, **overrides):
        values = dict(
            now=200,
            expected_audience="kmh-tool-gateway",
            expected_agent_id="agent-1",
            expected_workload_id="spiffe://kmh.test/agent-1",
            requested_scope="tool:read",
            requested_resource="document:123",
        )
        values.update(overrides)
        return self.validator.validate(signed or self.signed(self.mandate), **values)

    def test_valid_root_mandate(self):
        self.assertTrue(self.validate().valid)

    def test_signature_tampering_is_rejected(self):
        self.assertFalse(self.validate(SignedMandate(self.mandate, b"bad")).valid)

    def test_wrong_audience_is_rejected(self):
        self.assertFalse(self.validate(expected_audience="other-service").valid)

    def test_wrong_agent_or_workload_is_rejected(self):
        self.assertFalse(self.validate(expected_agent_id="other-agent").valid)
        self.assertFalse(self.validate(expected_workload_id="spiffe://other").valid)

    def test_not_yet_valid_and_expired_mandates_are_rejected(self):
        self.assertFalse(self.validate(now=99).valid)
        self.assertFalse(self.validate(now=500).valid)

    def test_overlong_mandate_is_rejected(self):
        long_lived = TaskMandate(**{
            **self.mandate.__dict__, "expires_at": 2_000,
            "nonce": "nonce-long",
        })
        self.assertFalse(self.validate(self.signed(long_lived)).valid)

    def test_scope_and_resource_escalation_are_rejected(self):
        self.assertFalse(self.validate(requested_scope="tool:admin").valid)
        self.assertFalse(self.validate(requested_resource="document:999").valid)

    def test_root_cannot_claim_parent_or_nonzero_depth(self):
        child_shaped_root = TaskMandate(**{
            **self.mandate.__dict__, "parent_mandate_id": "parent",
            "delegation_depth": 1, "nonce": "nonce-bad-root",
        })
        self.assertFalse(self.validate(self.signed(child_shaped_root)).valid)

    def test_delegated_mandate_must_attenuate_parent(self):
        parent_result = self.validate()
        self.assertTrue(parent_result.valid)
        parent = parent_result.verified_mandate
        child = TaskMandate(
            mandate_id="m-child", issuer="agent-1",
            subject_agent_id="agent-2",
            actor_workload_id="spiffe://kmh.test/agent-2",
            task_id="task-1", audience="kmh-tool-gateway",
            scopes=frozenset({"tool:read"}),
            resources=frozenset({"document:123"}),
            issued_at=150, not_before=150, expires_at=400,
            nonce="nonce-child-1", key_id="test-key",
            parent_mandate_id="m-root", delegation_depth=1,
            max_delegation_depth=2,
        )
        self.assertTrue(self.validate(
            self.signed(child),
            expected_agent_id="agent-2",
            expected_workload_id="spiffe://kmh.test/agent-2",
            requested_scope="tool:read",
            requested_resource="document:123",
            parent=parent,
        ).valid)

    def test_child_cannot_widen_parent_scope_or_resource_or_expiry(self):
        parent_result = self.validate()
        self.assertTrue(parent_result.valid)
        parent = parent_result.verified_mandate
        variants = [
            {"scopes": frozenset({"tool:admin"})},
            {"resources": frozenset({"document:999"})},
            {"expires_at": 600},
        ]
        for index, change in enumerate(variants):
            values = {
                "mandate_id": f"m-child-{index}", "issuer": "agent-1",
                "subject_agent_id": "agent-2",
                "actor_workload_id": "spiffe://kmh.test/agent-2",
                "task_id": "task-1", "audience": "kmh-tool-gateway",
                "scopes": frozenset({"tool:read"}),
                "resources": frozenset({"document:123"}),
                "issued_at": 150, "not_before": 150, "expires_at": 400,
                "nonce": f"nonce-child-{index}", "key_id": "test-key",
                "parent_mandate_id": "m-root", "delegation_depth": 1,
                "max_delegation_depth": 2,
            }
            values.update(change)
            child = TaskMandate(**values)
            result = self.validate(
                self.signed(child),
                expected_agent_id="agent-2",
                expected_workload_id="spiffe://kmh.test/agent-2",
                parent=parent,
            )
            self.assertFalse(result.valid, msg=str(change))

    def test_nonce_replay_is_rejected(self):
        first = self.validate()
        second = self.validate()
        self.assertTrue(first.valid)
        self.assertFalse(second.valid)

    def test_delegation_depth_policy_is_enforced(self):
        too_deep = TaskMandate(**{
            **self.mandate.__dict__, "max_delegation_depth": 4,
            "nonce": "nonce-too-deep",
        })
        self.assertFalse(self.validate(self.signed(too_deep)).valid)


if __name__ == "__main__":
    unittest.main()
