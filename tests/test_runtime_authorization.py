import unittest
from datetime import datetime, timezone

from src.authorization import (
    AgentIdentity,
    AuthorizationRequest,
    DelegationGrant,
    PolicyDecisionPoint,
    PolicyRule,
    PrincipalIdentity,
)
from src.components import OIARuntime
from src.recovery import DeterministicRecoveryPolicy, RecoveryConfig, RetryableExecutionError
from src.tools import ToolRequest, ToolResult


NOW = datetime(2026, 11, 7, 8, 0, tzinfo=timezone.utc)


class CountingExecutor:
    def __init__(self):
        self.calls = 0

    def execute(self, request: ToolRequest) -> ToolResult:
        self.calls += 1
        return ToolResult(request.tool_name, request.input_text, True, "counted")


def valid_request(request_id="runtime-request-1", tool_name="echo"):
    principal = PrincipalIdentity(
        subject="user:alice",
        tenant_id="tenant:one",
        issuer="https://identity.example",
        authenticated=True,
        active=True,
        authentication_method="oidc",
    )
    return AuthorizationRequest(
        request_id=request_id,
        principal=principal,
        actor=AgentIdentity(
            subject="user:alice",
            issuer="https://identity.example",
            active=True,
        ),
        tenant_id="tenant:one",
        action="read",
        resource="demo:resource",
        tool_name=tool_name,
        policy_version="runtime-v1",
    )


def pdp():
    return PolicyDecisionPoint(
        "runtime-v1",
        (PolicyRule("read", "demo:resource", "echo"),),
    )


class RuntimeAuthorizationEnforcementTests(unittest.TestCase):
    def test_valid_pdp_decision_allows_tool_execution(self):
        executor = CountingExecutor()
        runtime = OIARuntime(
            registry=executor,
            authorization_pdp=pdp(),
            authorization_clock=lambda: NOW,
        )
        output, stages, events = runtime.execute_detailed(
            "hello",
            authorization_request=valid_request(),
        )
        self.assertEqual(output, "hello")
        self.assertEqual(executor.calls, 1)
        self.assertIn("authorization", stages)
        auth_event = next(e for e in events if e.stage == "authorization")
        self.assertEqual(auth_event.status, "ok")
        self.assertEqual(auth_event.metadata["reason_code"], "ALLOW")

    def test_missing_context_blocks_before_executor(self):
        executor = CountingExecutor()
        runtime = OIARuntime(
            registry=executor,
            authorization_pdp=pdp(),
            authorization_clock=lambda: NOW,
        )
        with self.assertRaises(PermissionError):
            runtime.execute_detailed("hello")
        self.assertEqual(executor.calls, 0)

    def test_authorization_request_id_is_bound_to_execution_trace(self):
        executor = CountingExecutor()
        runtime = OIARuntime(
            registry=executor,
            authorization_pdp=pdp(),
            authorization_clock=lambda: NOW,
        )
        request = valid_request("trace-bound-request")
        _, _, events = runtime.execute_detailed(
            "hello", authorization_request=request
        )
        self.assertEqual(events[0].metadata["request_id"], request.request_id)
        self.assertEqual(executor.calls, 1)

    def test_tool_binding_mismatch_blocks_before_executor(self):
        executor = CountingExecutor()
        runtime = OIARuntime(
            registry=executor,
            authorization_pdp=pdp(),
            authorization_clock=lambda: NOW,
        )
        with self.assertRaises(PermissionError):
            runtime.execute_detailed(
                "hello",
                authorization_request=valid_request(tool_name="shell"),
            )
        self.assertEqual(executor.calls, 0)

    def test_authorization_is_revalidated_on_each_retry_attempt(self):
        class FlakyExecutor:
            def __init__(self):
                self.calls = 0

            def execute(self, request):
                self.calls += 1
                if self.calls == 1:
                    raise RetryableExecutionError("synthetic transient failure")
                return ToolResult(request.tool_name, request.input_text, True, "ok")

        actor = AgentIdentity(
            subject="agent:writer",
            issuer="https://agents.example",
            active=True,
        )
        delegated = AuthorizationRequest(
            request_id="retry-request",
            principal=PrincipalIdentity(
                subject="user:alice",
                tenant_id="tenant:one",
                issuer="https://identity.example",
                authenticated=True,
                active=True,
                authentication_method="oidc",
            ),
            actor=actor,
            tenant_id="tenant:one",
            action="write",
            resource="demo:resource",
            tool_name="echo",
            policy_version="runtime-v1",
            delegation=DelegationGrant(
                delegation_id="delegation:retry",
                issuer_subject="user:alice",
                subject="agent:writer",
                tenant_id="tenant:one",
                audience="echo",
                scopes=("write:demo:resource",),
                not_before=NOW,
                expires_at=NOW.replace(second=5),
            ),
            approval_reference="human-approval:1",
        )
        ticks = iter((NOW, NOW.replace(second=6)))
        executor = FlakyExecutor()
        runtime = OIARuntime(
            registry=executor,
            authorization_pdp=PolicyDecisionPoint(
                "runtime-v1",
                (PolicyRule("write", "demo:resource", "echo", True),),
            ),
            authorization_clock=lambda: next(ticks),
            recovery=DeterministicRecoveryPolicy(RecoveryConfig(max_attempts=2)),
        )

        with self.assertRaises(PermissionError):
            runtime.execute_detailed("hello", authorization_request=delegated)
        self.assertEqual(executor.calls, 1)

    def test_tenant_mismatch_blocks_before_executor(self):
        executor = CountingExecutor()
        runtime = OIARuntime(
            registry=executor,
            authorization_pdp=pdp(),
            authorization_clock=lambda: NOW,
        )
        request = valid_request()
        request = AuthorizationRequest(
            request_id=request.request_id,
            principal=request.principal,
            actor=request.actor,
            tenant_id="tenant:other",
            action=request.action,
            resource=request.resource,
            tool_name=request.tool_name,
            policy_version=request.policy_version,
        )
        with self.assertRaises(PermissionError):
            runtime.execute_detailed("hello", authorization_request=request)
        self.assertEqual(executor.calls, 0)


if __name__ == "__main__":
    unittest.main()
