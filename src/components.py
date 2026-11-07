"""Explicit component boundaries for the first KMH OIA runtime slice."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol

from src.agent import Agent, AgentRequest, DeterministicAgent
from src.autonomy_policy import AutonomyPolicy
from src.authorization import AuthorizationRequest, PolicyDecisionPoint
from src.errors import DeterministicErrorBoundary, ErrorBoundary
from src.evaluation import DeterministicEvaluator, Evaluator
from src.knowledge import KnowledgeSource, StaticKnowledgeSource
from src.memory import InMemoryMemoryStore, MemoryStore
from src.recovery import DeterministicRecoveryPolicy, RecoveryPolicy
from src.response import DeterministicResponder, Responder
from src.security import SecurityPolicy, ToolSecurityPolicy
from src.state import StateStore, StateStoreContract
from src.tools import ToolExecutor, ToolRegistry, ToolRequest, ToolResult
from src.trace import ExecutionContext, InMemoryTracer, TraceEvent, Tracer
from src.workflow import DeterministicOIACore, DeterministicWorkflow, OIACore, Workflow


@dataclass(frozen=True)
class RuntimeContext:
    goal: str
    session_id: str = "default"


class InputGatewayContract(Protocol):
    def accept(self, goal: str) -> RuntimeContext: ...


class ContextAssemblyContract(Protocol):
    def build(self, context: RuntimeContext) -> dict[str, str]: ...


class InputGateway:
    def accept(self, goal: str) -> RuntimeContext:
        if not goal.strip():
            raise ValueError("goal must not be empty")
        return RuntimeContext(goal=goal.strip())


class ContextAssembly:
    def __init__(self, memory: MemoryStore | None = None, knowledge: KnowledgeSource | None = None) -> None:
        self.memory = memory or InMemoryMemoryStore()
        self.knowledge = knowledge or StaticKnowledgeSource()

    def build(self, context: RuntimeContext) -> dict[str, str]:
        memories = self.memory.retrieve(context.session_id)
        knowledge = self.knowledge.retrieve(context.goal)
        return {
            "goal": context.goal,
            "memory": "; ".join(f"{item.key}={item.value}" for item in memories),
            "knowledge": "; ".join(f"[{item.source}] {item.content}" for item in knowledge),
        }


class GovernedTool:
    """PEP boundary: evaluate identity policy immediately before tool execution.

    When a PDP is configured, missing or mismatched authorization context is
    denied. The legacy allowlist remains available only when no PDP is injected.
    """

    def __init__(
        self,
        security: SecurityPolicy | None = None,
        registry: ToolExecutor | None = None,
        recovery: RecoveryPolicy | None = None,
        authorization_pdp: PolicyDecisionPoint | None = None,
        authorization_clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.security = security or ToolSecurityPolicy()
        self.registry = registry or ToolRegistry()
        self.recovery = recovery or DeterministicRecoveryPolicy()
        self.authorization_pdp = authorization_pdp
        self.authorization_clock = authorization_clock or (lambda: datetime.now(timezone.utc))

    def execute(
        self,
        request: ToolRequest,
        authorization_request: AuthorizationRequest | None = None,
    ) -> ToolResult:
        def execute_once() -> ToolResult:
            # Re-evaluate on every retry attempt; never reuse a stale ALLOW.
            if self.authorization_pdp is not None:
                if authorization_request is None:
                    return ToolResult(
                        request.tool_name, "", False,
                        "authorization context is required when PDP enforcement is enabled",
                    )
                if authorization_request.tool_name != request.tool_name:
                    return ToolResult(
                        request.tool_name, "", False,
                        "authorization tool binding mismatch",
                    )
                decision = self.authorization_pdp.evaluate(
                    authorization_request, now=self.authorization_clock()
                )
                if not decision.allowed:
                    return ToolResult(
                        request.tool_name, "", False,
                        f"authorization denied: {decision.reason_code}",
                    )

            decision = self.security.authorize(request.tool_name)
            if not decision.allowed:
                return ToolResult(request.tool_name, "", False, decision.reason)
            return self.registry.execute(request)

        return self.recovery.run(execute_once)


class OIARuntime:
    def __init__(
        self,
        state: StateStoreContract | None = None,
        security: SecurityPolicy | None = None,
        registry: ToolExecutor | None = None,
        agent: Agent | None = None,
        evaluator: Evaluator | None = None,
        responder: Responder | None = None,
        tracer: Tracer | None = None,
        core: OIACore | None = None,
        workflow: Workflow | None = None,
        gateway: InputGatewayContract | None = None,
        context_assembly: ContextAssemblyContract | None = None,
        error_boundary: ErrorBoundary | None = None,
        memory: MemoryStore | None = None,
        knowledge: KnowledgeSource | None = None,
        recovery: RecoveryPolicy | None = None,
        autonomy_policy: AutonomyPolicy | None = None,
        autonomy_scope: str = "local",
        authorization_pdp: PolicyDecisionPoint | None = None,
        authorization_clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.state = state or StateStore()
        self.memory = memory or InMemoryMemoryStore()
        self.knowledge = knowledge or StaticKnowledgeSource()
        self.gateway = gateway or InputGateway()
        self.context = context_assembly or ContextAssembly(self.memory, self.knowledge)
        self.core = core or DeterministicOIACore()
        self.workflow = workflow or DeterministicWorkflow()
        self.authorization_pdp = authorization_pdp
        self.tool = GovernedTool(
            security, registry, recovery, authorization_pdp, authorization_clock
        )
        self.autonomy_policy = autonomy_policy or AutonomyPolicy({"echo"}, {"local"})
        self.autonomy_scope = autonomy_scope
        self.agent = agent or DeterministicAgent()
        self.evaluator = evaluator or DeterministicEvaluator()
        self.responder = responder or DeterministicResponder()
        self.tracer = tracer or InMemoryTracer()
        self.error_boundary = error_boundary or DeterministicErrorBoundary()

    def execute(
        self,
        goal: str,
        session_id: str = "default",
        tool_name: str | None = "echo",
        authorization_request: AuthorizationRequest | None = None,
    ) -> tuple[str, list[str]]:
        output, stages, _ = self.execute_detailed(
            goal, session_id, tool_name, authorization_request
        )
        return output, stages

    def execute_detailed(
        self,
        goal: str,
        session_id: str = "default",
        tool_name: str | None = "echo",
        authorization_request: AuthorizationRequest | None = None,
    ) -> tuple[str, list[str], list[TraceEvent]]:
        stages: list[str] = []
        execution = ExecutionContext.create(
            session_id,
            request_id=authorization_request.request_id if authorization_request else None,
        )
        ids = {
            "request_id": execution.request_id,
            "session_id": execution.session_id,
            "workflow_id": execution.workflow_id,
            "task_id": execution.task_id,
            "agent_id": execution.agent_id,
            "trace_id": execution.trace_id,
        }

        def emit(stage: str, status: str = "ok", **metadata: str) -> None:
            event = TraceEvent(stage, status, {**ids, "status": status, **metadata})
            stages.append(stage)
            self.tracer.emit(event)

        state_snapshot = self.state.snapshot(session_id)
        memory_snapshot = self.memory.snapshot(session_id)
        try:
            emit("input_gateway")
            accepted = self.gateway.accept(goal)
            emit("oia_core")
            core_context = self.core.build_context(accepted.goal)
            context = self.context.build(RuntimeContext(core_context["goal"], session_id))
            emit(
                "context_assembly",
                memory_chars=str(len(context.get("memory", ""))),
                knowledge_chars=str(len(context.get("knowledge", ""))),
            )
            emit("workflow")
            agent_request = self.workflow.prepare(context)
            agent_request = AgentRequest(agent_request.goal, context)
            decision = self.agent.decide(agent_request)
            emit("agent", tool=decision.tool_name, reason=decision.reason)
            self.state.set(session_id, "last_goal", context["goal"])
            self.memory.update(session_id, "last_goal", context["goal"])
            emit("state", memory_updated="true")

            selected_tool = tool_name if tool_name is not None else decision.tool_name
            autonomy = self.autonomy_policy.evaluate(selected_tool, self.autonomy_scope)
            if not autonomy.allowed:
                emit(
                    "tool_security", status="blocked", tool=selected_tool,
                    reason=autonomy.reason, autonomy_status="blocked",
                    autonomy_action=selected_tool, autonomy_scope=self.autonomy_scope,
                    autonomy_reason=autonomy.reason,
                )
                raise PermissionError(autonomy.reason)

            if self.authorization_pdp is not None and authorization_request is None:
                emit(
                    "authorization", status="blocked",
                    reason_code="AUTHORIZATION_CONTEXT_REQUIRED",
                    policy_version="unknown",
                )
                raise PermissionError("authorization context is required")

            if authorization_request is not None:
                if authorization_request.request_id != execution.request_id:
                    emit(
                        "authorization", status="blocked",
                        reason_code="REQUEST_ID_BINDING_MISMATCH",
                        policy_version=authorization_request.policy_version,
                    )
                    raise PermissionError("authorization request ID binding mismatch")
                if authorization_request.tool_name != selected_tool:
                    emit(
                        "authorization", status="blocked",
                        reason_code="TOOL_BINDING_MISMATCH",
                        policy_version=authorization_request.policy_version,
                    )
                    raise PermissionError("authorization tool binding mismatch")

            result = self.tool.execute(
                ToolRequest(selected_tool, decision.input_text),
                authorization_request=authorization_request,
            )
            emit(
                "authorization",
                status="ok" if result.success and self.authorization_pdp is not None else (
                    "blocked" if self.authorization_pdp is not None else "not_configured"
                ),
                reason_code="ALLOW" if result.success and self.authorization_pdp is not None else (
                    "DENIED_OR_TOOL_REJECTED" if self.authorization_pdp is not None else "PDP_NOT_CONFIGURED"
                ),
                policy_version=authorization_request.policy_version if authorization_request else "unknown",
            )
            emit(
                "tool_security",
                status="ok" if result.success else "blocked",
                tool=selected_tool,
                reason=result.reason,
                autonomy_status="ok",
                autonomy_action=selected_tool,
                autonomy_scope=self.autonomy_scope,
                autonomy_reason=autonomy.reason,
            )
            if not result.success:
                raise PermissionError(result.reason)
            emit("governed_tool", tool=selected_tool)
            evaluation = self.evaluator.evaluate(result)
            emit("evaluation", status="ok" if evaluation.accepted else "rejected", reason=evaluation.reason)
            if not evaluation.accepted:
                raise ValueError(evaluation.reason)
            response = self.responder.render(result.output_text)
            self.memory.update(session_id, "last_response", response.text)
            emit("response", memory_updated="true")
            emit("trace", event_count=str(len(stages) + 1))
            return response.text, stages, self.tracer.events
        except Exception as error:
            self.state.restore(session_id, state_snapshot)
            self.memory.restore(session_id, memory_snapshot)
            emit("rollback", status="ok")
            info = self.error_boundary.classify(error)
            emit("error", status=info.category.value, reason=info.message, recoverable=str(info.recoverable).lower())
            raise
