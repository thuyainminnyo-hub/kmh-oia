import unittest

from src.agent_trust import AgentIdentity, AgentTrustRegistry, DelegationGrant, HumanApproval
from src.components import OIARuntime


class RuntimeAgentTrustIntegrationTests(unittest.TestCase):
    def make_registry(self, scopes):
        registry = AgentTrustRegistry()
        registry.register_agent(
            AgentIdentity("runtime-agent", "owner-1", "oia-runtime", "test")
        )
        registry.add_root_grant(DelegationGrant(
            "runtime-root", "owner-1", "runtime-agent",
            frozenset(scopes), 4_102_444_800,
        ))
        return registry

    def test_runtime_requires_trust_identity_and_scope_mapping(self):
        runtime = OIARuntime(
            trust_registry=self.make_registry({"tool:echo"}),
            trust_agent_id="runtime-agent",
        )
        with self.assertRaises(PermissionError):
            runtime.execute_detailed("hello")

    def test_runtime_blocks_tool_without_delegated_scope(self):
        runtime = OIARuntime(
            trust_registry=self.make_registry({"content:read"}),
            trust_agent_id="runtime-agent",
            trust_scopes={"echo": "tool:echo"},
        )
        with self.assertRaises(PermissionError):
            runtime.execute_detailed("hello")


    def test_runtime_sensitive_action_requires_request_bound_human_approval(self):
        registry = AgentTrustRegistry(sensitive_tools=frozenset({"echo"}))
        registry.register_agent(
            AgentIdentity("runtime-agent", "owner-1", "oia-runtime", "test")
        )
        registry.add_root_grant(DelegationGrant(
            "runtime-root", "owner-1", "runtime-agent",
            frozenset({"tool:echo"}), 4_102_444_800,
        ))
        runtime = OIARuntime(
            trust_registry=registry,
            trust_agent_id="runtime-agent",
            trust_scopes={"echo": "tool:echo"},
        )
        with self.assertRaises(PermissionError):
            runtime.execute_detailed("hello", request_id="approval-req-1")
        approval = HumanApproval(
            "approval-req-1", "runtime-agent", "echo", "local", "human-owner", True
        )
        response, _, _ = runtime.execute_detailed(
            "hello", request_id="approval-req-1", human_approval=approval
        )
        self.assertEqual(response, "hello")
        with self.assertRaises(PermissionError):
            runtime.execute_detailed(
                "hello", request_id="approval-req-1", human_approval=approval
            )

    def test_runtime_authorizes_tool_at_execution_boundary(self):
        runtime = OIARuntime(
            trust_registry=self.make_registry({"tool:echo"}),
            trust_agent_id="runtime-agent",
            trust_scopes={"echo": "tool:echo"},
        )
        response, stages, events = runtime.execute_detailed("hello")
        self.assertEqual(response, "hello")
        self.assertIn("governed_tool", stages)
        self.assertTrue(any(event.stage == "governed_tool" for event in events))


if __name__ == "__main__":
    unittest.main()
