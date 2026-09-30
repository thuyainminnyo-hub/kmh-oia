"""Explicit component boundaries for the first KMH OIA runtime slice."""

from dataclasses import dataclass

from src.agent import Agent, AgentRequest, DeterministicAgent
from src.evaluation import DeterministicEvaluator, Evaluator
from src.security import ToolSecurityPolicy
from src.state import StateStore, StateStoreContract
from src.tools import ToolExecutor, ToolRegistry, ToolRequest, ToolResult


@dataclass(frozen=True)
class RuntimeContext:
    goal: str


@dataclass(frozen=True)
class TraceEvent:
    stage: str
    status: str
    metadata: dict[str, str]


class InputGateway:
    def accept(self, goal: str) -> RuntimeContext:
        if not goal.strip():
            raise ValueError("goal must not be empty")
        return RuntimeContext(goal=goal.strip())


class ContextAssembly:
    def build(self, context: RuntimeContext) -> dict[str, str]:
        return {"goal": context.goal}


class GovernedTool:
    def __init__(
        self,
        security: ToolSecurityPolicy | None = None,
        registry: ToolExecutor | None = None,
    ) -> None:
        self.security = security or ToolSecurityPolicy()
        self.registry = registry or ToolRegistry()

    def execute(self, request: ToolRequest) -> ToolResult:
        decision = self.security.authorize(request.tool_name)
        if not decision.allowed:
            return ToolResult(
                tool_name=request.tool_name,
                output_text="",
                success=False,
                reason=decision.reason,
            )
        return self.registry.execute(request)


class OIARuntime:
    def __init__(
        self,
        state: StateStoreContract | None = None,
        security: ToolSecurityPolicy | None = None,
        registry: ToolExecutor | None = None,
        agent: Agent | None = None,
        evaluator: Evaluator | None = None,
    ) -> None:
        self.state = state or StateStore()
        self.gateway = InputGateway()
        self.context = ContextAssembly()
        self.tool = GovernedTool(security, registry)
        self.agent = agent or DeterministicAgent()
        self.evaluator = evaluator or DeterministicEvaluator()

    def execute(
        self,
        goal: str,
        session_id: str = "default",
        tool_name: str | None = "echo",
    ) -> tuple[str, list[str]]:
        output, stages, _ = self.execute_detailed(goal, session_id, tool_name)
        return output, stages

    def execute_detailed(
        self,
        goal: str,
        session_id: str = "default",
        tool_name: str | None = "echo",
    ) -> tuple[str, list[str], list[TraceEvent]]:
        stages: list[str] = []
        events: list[TraceEvent] = []

        def emit(stage: str, status: str = "ok", **metadata: str) -> None:
            stages.append(stage)
            events.append(TraceEvent(stage, status, metadata))

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
        request = ToolRequest(tool_name=selected_tool, input_text=decision.input_text)
        result = self.tool.execute(request)
        emit(
            "tool_security",
            status="ok" if result.success else "blocked",
            tool=selected_tool,
            reason=result.reason,
        )
        if not result.success:
            raise PermissionError(result.reason)
        emit("governed_tool", tool=selected_tool)
        evaluation = self.evaluator.evaluate(result)
        emit("evaluation", status="ok" if evaluation.accepted else "rejected", reason=evaluation.reason)
        if not evaluation.accepted:
            raise ValueError(evaluation.reason)
        emit("response")
        emit("trace", event_count=str(len(events)))
        return result.output_text, stages, events
