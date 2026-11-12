import unittest

from src.agent_trust import (
    ActionRequest,
    AgentIdentity,
    AgentTrustRegistry,
    DelegationGrant,
    HumanApproval,
    InMemoryAppendOnlyAudit,
)


class AgentTrustRegistryTests(unittest.TestCase):
    def setUp(self):
        self.audit = InMemoryAppendOnlyAudit()
        self.registry = AgentTrustRegistry(audit=self.audit)
        self.registry.register_agent(AgentIdentity("planner", "owner-1", "planning", "test"))
        self.registry.register_agent(AgentIdentity("worker", "owner-1", "worker", "test"))
        self.registry.register_agent(AgentIdentity("worker-2", "owner-1", "worker", "test"))
        self.registry.add_root_grant(DelegationGrant(
            "root", "owner-1", "planner",
            frozenset({"content:read", "content:write", "publish"}),
            10_000,
        ))
        self.registry.delegate(DelegationGrant(
            "worker-read", "planner", "worker",
            frozenset({"content:read", "publish"}), 9_000, "root",
        ))
        self.registry.delegate(DelegationGrant(
            "worker-2-read", "planner", "worker-2",
            frozenset({"content:read"}), 9_000, "root",
        ))

    def request(self, **overrides):
        values = dict(
            request_id="req-1", agent_id="worker", tool_name="read",
            resource="content/item-1", required_scope="content:read",
        )
        values.update(overrides)
        return ActionRequest(**values)

    def test_delegated_agent_can_use_attenuated_scope(self):
        decision = self.registry.authorize(self.request(), now_epoch=100)
        self.assertTrue(decision.allowed)

    def test_delegated_agent_cannot_escalate_scope(self):
        decision = self.registry.authorize(
            self.request(required_scope="content:write"), now_epoch=100
        )
        self.assertFalse(decision.allowed)

    def test_delegation_cannot_exceed_parent_scope(self):
        with self.assertRaises(ValueError):
            self.registry.delegate(DelegationGrant(
                "bad-child", "planner", "worker",
                frozenset({"admin"}), 9_000, "root",
            ))

    def test_expired_grant_is_denied(self):
        decision = self.registry.authorize(self.request(), now_epoch=9_000)
        self.assertFalse(decision.allowed)

    def test_sensitive_action_requires_exact_human_approval(self):
        request = self.request(tool_name="publish", required_scope="publish")
        denied = self.registry.authorize(request, now_epoch=100)
        self.assertFalse(denied.allowed)
        approval = HumanApproval(
            "req-1", "worker", "publish", "content/item-1", "human-owner", True
        )
        allowed = self.registry.authorize(request, now_epoch=100, approval=approval)
        self.assertTrue(allowed.allowed)

    def test_approval_cannot_be_reused_for_different_resource(self):
        request = self.request(tool_name="publish", required_scope="publish")
        approval = HumanApproval(
            "req-1", "worker", "publish", "content/other", "human-owner", True
        )
        self.assertFalse(
            self.registry.authorize(request, now_epoch=100, approval=approval).allowed
        )


    def test_sensitive_approval_is_single_use(self):
        request = self.request(tool_name="publish", required_scope="publish")
        approval = HumanApproval(
            "req-1", "worker", "publish", "content/item-1", "human-owner", True
        )
        self.assertTrue(
            self.registry.authorize(request, now_epoch=100, approval=approval).allowed
        )
        replay = self.registry.authorize(request, now_epoch=100, approval=approval)
        self.assertFalse(replay.allowed)

    def test_revoked_agent_is_denied(self):
        self.registry.revoke_agent("worker")
        self.assertFalse(self.registry.authorize(self.request(), now_epoch=100).allowed)

    def test_denials_and_allows_are_audited_in_order(self):
        self.registry.authorize(self.request(), now_epoch=100)
        self.registry.authorize(
            self.request(request_id="req-2", required_scope="admin"), now_epoch=100
        )
        self.assertEqual([e.sequence for e in self.audit.events], [1, 2])
        self.assertEqual([e.decision for e in self.audit.events], ["allow", "deny"])


    def test_sibling_delegations_do_not_block_valid_branch(self):
        decision = self.registry.authorize(self.request(), now_epoch=100)
        self.assertTrue(decision.allowed)

    def test_revoked_delegating_agent_invalidates_descendant_grant(self):
        self.registry.revoke_agent("planner")
        decision = self.registry.authorize(self.request(), now_epoch=100)
        self.assertFalse(decision.allowed)

    def test_duplicate_agent_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.register_agent(
                AgentIdentity("worker", "owner-1", "worker", "test")
            )


if __name__ == "__main__":
    unittest.main()
