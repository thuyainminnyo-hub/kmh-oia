"""Explicit component boundaries for the first KMH OIA runtime slice."""

from dataclasses import dataclass

from src.agent import Agent, AgentRequest, DeterministicAgent
from src.evaluation import DeterministicEvaluator, Evaluator
from src.response import DeterministicResponder, Responder
from src.security import ToolSecurityPolicy
from src.state import StateStore, StateStoreContract
from src.tools import ToolExecutor, ToolRegistry, ToolRequest, ToolResult
from src.trace import InMemoryTracer, TraceEvent, Tracer


@dataclass(frozen=True)
class RuntimeContext:
    goal: str


class InputGateway:
    def accept(self, goal: str) -> RuntimeContext:
        if not goal.strip(): raise ValueError("goal must not be empty")
        return RuntimeContext(goal=goal.strip())


class ContextAssembly:
    def build(self, context: RuntimeContext) -> dict[str, str]:
        return {"goal": context.goal}


class GovernedTool:
    def __init__(self, security: ToolSecurityPolicy | None = None, registry: ToolExecutor | None = None) -> None:
        self.security = security or ToolSecurityPolicy()
        self.registry = registry or ToolRegistry()

    def execute(self, request: ToolRequest) -> ToolResult:
        decision = self.security.authorize(request.tool_name)
        if not decision.allowed:
            return ToolResult(request.tool_name, "", False, decision.reason)
        return self.registry.execute(request)


class OIARuntime:
    def __init__(self, state: StateStoreContract | None = None, security: ToolSecurityPolicy | None = None,
                 registry: ToolExecutor | None = None, agent: Agent | None = None,
                 evaluator: Evaluator | None = None, responder: Responder | None = None,
                 tracer: Tracer | None = None) -> None:
        self.state = state or StateStore()
        self.gateway = InputGateway()
        self.context = ContextAssembly()
        self.tool = GovernedTool(security, registry)
        self.agent = agent or DeterministicAgent()
        self.evaluator = evaluator or DeterministicEvaluator()
        self.responder = responder or DeterministicResponder()
        self.tracer = tracer or InMemoryTracer()

    def execute(self, goal: str, session_id: str = "default", tool_name: str | None = "echo") -> tuple[str, list[str]]:
        output, stages, _ = self.execute_detailed(goal, session_id, tool_name)
        return output, stages

    def execute_detailed(self, goal: str, session_id: str = "default", tool_name: str | None = "echo") -> tuple[str, list[str], list[TraceEvent]]:
        stages: list[str] = []
        def emit(stage: str, status: str = "ok", **metadata: str) -> None:
            event = TraceEvent(stage, status, metadata)
            stages.append(stage)
            self.tracer.emit(event)
        emit("input_gateway")
        accepted = self.gateway.accept(goal)
        emit("oia_core")
        context = self.context.build(accepted)
        emit("context_assembly")
        emit("workflow")
        decision = self.agent.decide(AgentRequest(context["goal"]))
        emit("agent", tool=decision.tool_name, reason=decision.reason)
        self.state.set(session_id, "last_goal", context["goal"])
        emit("state", session_id=session_id)
        selected_tool = tool_name if tool_name is not None else decision.tool_name
        result = self.tool.execute(ToolRequest(selected_tool, decision.input_text))
        emit("tool_security", status="ok" if result.success else "blocked", tool=selected_tool, reason=result.reason)
        if not result.success: raise PermissionError(result.reason)
        emit("governed_tool", tool=selected_tool)
        evaluation = self.evaluator.evaluate(result)
        emit("evaluation", status="ok" if evaluation.accepted else "rejected", reason=evaluation.reason)
        if not evaluation.accepted: raise ValueError(evaluation.reason)
        response = self.responder.render(result.output_text)
        emit("response")
        emit("trace", event_count=str(len(stages) + 1))
        return response.text, stages, self.tracer.events
